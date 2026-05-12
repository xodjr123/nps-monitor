import requests
import json
import os
from datetime import datetime, timedelta

# --- 설정 (GitHub Secrets) ---
DART_API_KEY = os.environ.get("DART_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DB_FILE = "last_disclosure.json"

def get_nps_disclosures():
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        'crtfc_key': DART_API_KEY,
        'bgn_de': (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
        'pblntf_ty': 'B',
        'corp_code': '00126380',
        'page_count': '20'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data.get('list', []) if data['status'] == '000' else []
    except:
        return []

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def load_last_rcept_no():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f).get('rcept_no')
        except:
            return None
    return None

def save_last_rcept_no(rcept_no):
    with open(DB_FILE, 'w') as f:
        json.dump({'rcept_no': rcept_no}, f)

def monitor():
    disclosures = get_nps_disclosures()
    if not disclosures:
        return

    last_rcept_no = load_last_rcept_no()
    new_disclosures = []

    # 오래된 공시부터 순서대로 체크
    for d in reversed(disclosures):
        if "주식등의대량보유상황보고서" in d['report_nm']:
            # 마지막으로 본 번호보다 최신인 경우만 추가
            if last_rcept_no is None or d['rcept_no'] > last_rcept_no:
                new_disclosures.append(d)

    for d in new_disclosures:
        msg = (
            f"🚨 <b>국민연금 새 공시 발생</b>\n\n"
            f"기업명: {d['corp_name']}\n"
            f"보고서: {d['report_nm']}\n"
            f"날짜: {d['rcept_dt']}\n"
            f"링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d['rcept_no']}"
        )
        send_telegram_message(msg)
        last_rcept_no = d['rcept_no']

    if new_disclosures:
        save_last_rcept_no(last_rcept_no)

if __name__ == "__main__":
    monitor()
    
