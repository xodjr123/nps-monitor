import requests
import json
import os
from datetime import datetime, timedelta

DART_API_KEY = os.environ.get("DART_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DB_FILE = "last_disclosure.json"

def get_nps_disclosures():
    all_list = []
    url = "https://opendart.fss.or.kr/api/list.json"

    # 10페이지(총 1,000건)까지 확인하여 연휴나 공시 폭주 시기에도 대비합니다.
    for page in range(1, 11):
        params = {
            'crtfc_key': DART_API_KEY,
            'bgn_de': (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
            'pblntf_ty': 'B',
            'page_no': str(page),
            'page_count': '100'
        }
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data['status'] == '000':
                all_list.extend(data.get('list', []))
                if len(data.get('list', [])) < 100: break
            else: break
        except: break
    return all_list

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def load_last_rcept_no():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: return json.load(f).get('rcept_no')
        except: return None
    return None

def save_last_rcept_no(rcept_no):
    with open(DB_FILE, 'w') as f: json.dump({'rcept_no': rcept_no}, f)

def monitor():
    disclosures = get_nps_disclosures()
    if not disclosures: return

    last_rcept_no = load_last_rcept_no()
    new_disclosures = []

    for d in reversed(disclosures):
        if "국민연금공단" in d['flr_nm']:
            if last_rcept_no is None or d['rcept_no'] > last_rcept_no:
                new_disclosures.append(d)

    for d in new_disclosures:
        msg = (
            f"🚨 <b>국민연금 새 공시 발생</b>\n\n"
            f"대상기업: {d['corp_name']}\n"
            f"보고서명: {d['report_nm']}\n"
            f"제출인: {d['flr_nm']}\n"
            f"접수일자: {d['rcept_dt']}\n"
            f"링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d['rcept_no']}"
        )
        send_telegram_message(msg)
        last_rcept_no = d['rcept_no']

    if new_disclosures:
        save_last_rcept_no(last_rcept_no)

if __name__ == "__main__":
    monitor()
