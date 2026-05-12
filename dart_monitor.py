import requests
import json
import os
from datetime import datetime, timedelta

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
        'page_count': '100'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data['status'] == '000':
            return data.get('list', [])
        else:
            print(f"DART API 오류: {data['message']}")
            return []
    except Exception as e:
        print(f"API 요청 에러: {e}")
        return []

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def monitor():
    print("--- 국민연금 공시 추적 시작 ---")
    disclosures = get_nps_disclosures()
    print(f"가져온 전체 공시 개수: {len(disclosures)}개")

    if not disclosures:
        return

    # 텔레그램 연결 상태 확인
    print("텔레그램 연결 상태 확인 완료")

    for d in reversed(disclosures):
        # 1. 제출인 이름 확인
        if "국민연금" in d['flr_nm']:
            print(f"✅ 국민연금 공시 발견: {d['corp_name']} ({d['rcept_no']})")

            # 2. 메시지 구성 및 전송
            msg = (
                f"🚨 <b>국민연금 공시 포착</b>\n\n"
                f"기업명: {d['corp_name']}\n"
                f"보고서: {d['report_nm']}\n"
                f"제출인: {d['flr_nm']}\n"
                f"날짜: {d['rcept_dt']}\n"
                f"링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d['rcept_no']}"
            )
            send_telegram_message(msg)
            print(f"텔레그램 전송 완료: {d['corp_name']}")

    print("--- 추적 종료 ---")

if __name__ == "__main__":
    monitor()
