import requests
import json
import os
from datetime import datetime, timedelta

DART_API_KEY = os.environ.get("DART_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_nps_disclosures():
    all_list = []
    url = "https://opendart.fss.or.kr/api/list.json"
    # 넉넉하게 14일 전부터 검색
    bgn_de = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')

    # 15페이지(총 1,500건)까지 확인하여 800건이 넘는 공시를 모두 훑습니다.
    for page in range(1, 16):
        params = {
            'crtfc_key': DART_API_KEY,
            'bgn_de': bgn_de,
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

def monitor():
    print("--- 국민연금 공시 전수 조사 시작 ---")
    disclosures = get_nps_disclosures()
    print(f"가져온 전체 공시 개수: {len(disclosures)}개")

    found_count = 0
    for d in reversed(disclosures):
        if "국민연금공단" in d['flr_nm']:
            msg = (
                f"🚨 <b>국민연금 공시 발견!</b>\n\n"
                f"대상기업: {d['corp_name']}\n"
                f"보고서명: {d['report_nm']}\n"
                f"제출인: {d['flr_nm']}\n"
                f"접수일자: {d['rcept_dt']}\n"
                f"링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d['rcept_no']}"
            )
            send_telegram_message(msg)
            print(f"전송 성공: {d['corp_name']}")
            found_count += 1

    print(f"총 {found_count}건 전송 완료")

if __name__ == "__main__":
    monitor()
