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
    # corp_code를 빼고 검색해야 '제출인' 기준 필터링이 가능합니다.
    params = {
        'crtfc_key': DART_API_KEY,
        'bgn_de': (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
        'pblntf_ty': 'B', # 주식등의대량보유상황보고서
        'page_count': '100' # 최근 100개를 가져와서 필터링
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data['status'] == '000':
            return data.get('list', [])
        return []
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
        print("공시 목록을 가져오지 못했습니다.")
        return

    last_rcept_no = load_last_rcept_no()
    found_count = 0

    # 최신순이므로 역순(오래된 것부터) 처리
    for d in reversed(disclosures):
        # 제출인(flr_nm)이 '국민연금공단'인 경우만 필터링
        if "국민연금공단" in d['flr_nm']:
            if last_rcept_no is None or d['rcept_no'] > last_rcept_no:
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
                found_count += 1

    if found_count > 0:
        save_last_rcept_no(last_rcept_no)
        print(f"{found_count}개의 새로운 국민연금 공시를 전송했습니다.")
    else:
        print("새로운 국민연금 공시가 없습니다.")

if __name__ == "__main__":
    monitor()
