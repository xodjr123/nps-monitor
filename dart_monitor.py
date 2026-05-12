import requests
import json
import os
from datetime import datetime, timedelta

DART_API_KEY = os.environ.get("DART_API_KEY", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def get_nps_disclosures():
    all_list = []
    url = "https://opendart.fss.or.kr/api/list.json"
    bgn_de = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')

    # 국민연금공단의 고유번호(00126380)를 직접 지정하여 검색합니다.
    # 이렇게 하면 국민연금이 '제출인'으로서 올린 모든 주식 보고서가 나옵니다.
    params = {
        'crtfc_key': DART_API_KEY,
        'corp_code': '00126380',
        'bgn_de': bgn_de,
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
        print(f"에러 발생: {e}")
        return []

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def monitor():
    print("--- 국민연금 직접 추적 시작 ---")
    disclosures = get_nps_disclosures()
    print(f"국민연금이 작성한 공시 총 {len(disclosures)}건 발견")

    # 발견된 모든 공시를 텔레그램으로 전송
    for d in reversed(disclosures):
        # 우리가 찾는 '주식등의대량보유상황보고서'만 필터링
        if "주식등의대량보유상황보고서" in d['report_nm']:
            print(f"✅ 전송 중: {d['corp_name']}")
            msg = (
                f"🚨 <b>국민연금 공시 발견!</b>\n\n"
                f"기업명: {d['corp_name']}\n"
                f"보고서: {d['report_nm']}\n"
                f"날짜: {d['rcept_dt']}\n"
                f"링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d['rcept_no']}"
            )
            send_telegram_message(msg)

    print("--- 작업 완료 ---")

if __name__ == "__main__":
    monitor()
