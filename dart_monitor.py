import requests
import json
import os
import time
from datetime import datetime, timedelta

# --- 설정 (GitHub Secrets에서 불러옵니다) ---
DART_API_KEY = os.environ.get("DART_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DB_FILE = "last_disclosure.json"
# ------------------------------------------

def get_nps_disclosures():
    """국민연금공단의 대량보유 공시를 가져옵니다."""
    url = "https://opendart.fss.or.kr/api/list.json"
    
    # 국민연금공단 고유번호는 보통 '00126380' 입니다. 
    # 혹은 이름(nm)으로 검색할 수도 있습니다.
    params = {
        'crtfc_key': DART_API_KEY,
        'bgn_de': (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'), # 최근 7일치
        'pblntf_ty': 'B', # 대량보유상황보고서 타입
        'corp_code': '00126380', # 국민연금공단 고유번호
        'page_count': '10'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == '000':
            return data['list']
        else:
            print(f"DART API 오류: {data['message']}")
            return []
    except Exception as e:
        print(f"요청 중 오류 발생: {e}")
        return []

def send_telegram_message(message):
    """텔레그램으로 메시지를 보냅니다."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.post(url, data=payload)

def load_last_rcept_no():
    """마지막으로 알림을 보낸 접수번호를 불러옵니다."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f).get('rcept_no')
    return None

def save_last_rcept_no(rcept_no):
    """최신 접수번호를 저장합니다."""
    with open(DB_FILE, 'w') as f:
        json.dump({'rcept_no': rcept_no}, f)

def monitor():
    print(f"[{datetime.now()}] 모니터링 중...")
    disclosures = get_nps_disclosures()
    
    if not disclosures:
        return

    last_rcept_no = load_last_rcept_no()
    
    # 최신순으로 정렬되어 있으므로 역순(오래된 것부터)으로 체크
    new_disclosures = []
    for d in reversed(disclosures):
        # '주식등의대량보유상황보고서'가 포함된 제목만 필터링
        if "주식등의대량보유상황보고서" in d['report_nm']:
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
        print(f"새 알림 전송: {d['corp_name']}")
        last_rcept_no = d['rcept_no']

    if new_disclosures:
        save_last_rcept_no(last_rcept_no)

if __name__ == "__main__":
    # 이 스크립트를 서버(GitHub Actions 등)에서 돌릴 때는 
    # 무한 루프 대신 한 번 실행하고 종료되게 설정하는 것이 좋습니다.
    monitor()
