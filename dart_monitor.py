import requests
import json
import os
from datetime import datetime, timedelta

# --- 설정 (공백 제거 처리 추가) ---
DART_API_KEY = os.environ.get("DART_API_KEY", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def get_nps_disclosures():
    all_list = []
    url = "https://opendart.fss.or.kr/api/list.json"
    bgn_de = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')

    print(f"--- 데이터 수집 시작 (시작일: {bgn_de}) ---")

    for page in range(1, 16): # 15페이지까지 확인
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
            status = data.get('status')
            message = data.get('message')

            current_list = data.get('list', [])
            list_count = len(current_list)

            print(f"페이지 {page}: 상태={status}, 가져온 개수={list_count}")

            if status == '000':
                all_list.extend(current_list)
                if list_count < 100:
                    print("마지막 페이지에 도달했습니다.")
                    break
            else:
                print(f"⚠️ {page}페이지에서 오류 발생: {message}")
                break
        except Exception as e:
            print(f"❌ {page}페이지 요청 중 에러: {e}")
            break

    return all_list

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print(f"텔레그램 전송 실패: {r.text}")

def monitor():
    # 연결 테스트용 (가장 먼저 전송)
    send_telegram_message("📡 국민연금 감시 시스템 연결 확인!")

    disclosures = get_nps_disclosures()
    total_found = len(disclosures)
    print(f"총 수집된 공시: {total_found}개")

    nps_count = 0
    for d in reversed(disclosures):
        # '국민연금'이라는 글자가 포함되면 무조건 발송
        if "국민연금" in d['flr_nm']:
            nps_count += 1
            print(f"🎯 발견: {d['corp_name']} (제출인: {d['flr_nm']})")
            msg = (
                f"🚨 <b>국민연금 공시 발견!</b>\n\n"
                f"기업명: {d['corp_name']}\n"
                f"보고서: {d['report_nm']}\n"
                f"제출인: {d['flr_nm']}\n"
                f"날짜: {d['rcept_dt']}\n"
                f"링크: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d['rcept_no']}"
            )
            send_telegram_message(msg)

    print(f"--- 작업 완료: 국민연금 공시 {nps_count}건 전송 ---")

if __name__ == "__main__":
    monitor()
