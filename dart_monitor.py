import requests
import json
import os
from datetime import datetime, timedelta

DART_API_KEY = os.environ.get("DART_API_KEY", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
DB_FILE = "last_disclosure.json"

def get_nps_disclosures():
    all_list = []
    url = "https://opendart.fss.or.kr/api/list.json"
    bgn_de = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

    # 유형을 'D'(지분공시)로 설정해야 주식 대량보유 보고서가 나옵니다!
    for page in range(1, 11):
        params = {
            'crtfc_key': DART_API_KEY,
            'bgn_de': bgn_de,
            'pblntf_ty': 'D',
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
    print("--- 국민연금 지분공시 추적 시작 ---")
    disclosures = get_nps_disclosures()
    print(f"가져온 전체 지분공시 개수: {len(disclosures)}개")

    last_rcept_no = load_last_rcept_no()
    new_disclosures = []

    for d in reversed(disclosures):
        # 1. 제출인이 '국민연금공단'이고
        # 2. 보고서 제목에 '주식등의대량보유'가 포함된 것만 필터링
        if "국민연금공단" in d['flr_nm'] and "주식등의대량보유" in d['report_nm']:
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
        print(f"알림 전송: {d['corp_name']}")
        last_rcept_no = d['rcept_no']

    if new_disclosures:
        save_last_rcept_no(last_rcept_no)
        print(f"총 {len(new_disclosures)}건의 새 공시를 보냈습니다.")
    else:
        print("새로운 국민연금 공시가 없습니다.")

if __name__ == "__main__":
    monitor()
