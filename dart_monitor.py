import requests
import json
import os
from datetime import datetime, timedelta

# --- 설정 (GitHub Secrets에서 불러옵니다) ---
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
        'page_count': '30' # 테스트를 위해 개수를 넉넉히
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

def monitor():
    # 1. 연결 확인용 테스트 메시지 발송
    send_telegram_message("🚀 <b>국민연금 모니터링 테스트를 시작합니다!</b>")

    disclosures = get_nps_disclosures()

    if not disclosures:
        send_telegram_message("ℹ️ 최근 7일간 국민연금의 대량보유 공시가 없습니다.")
        return

    # 2. 테스트를 위해 '이미 읽은 공시' 체크를 건너뛰고 모두 발송
    for d in disclosures:
        if "주식등의대량보유상황보고서" in d['report_nm']:
            msg = (
                f"🚨 <b>국민연금 공시 발견 (테스트)</b>\n\n"
                f"기업명: {d['corp_name']}\n"
                f"보고서: {d['report_nm']}\n"
                f"날짜: {d['rcept_dt']}\n"
                f"링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d['rcept_no']}"
            )
            send_telegram_message(msg)

    send_telegram_message("✅ 모든 테스트 발송이 완료되었습니다.")

if __name__ == "__main__":
    monitor()
