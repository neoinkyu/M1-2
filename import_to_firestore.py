import argparse
import os

import firebase_admin
import gspread
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from google.oauth2.service_account import Credentials


# --------------------------------------------------
# 환경 변수
# --------------------------------------------------

load_dotenv()

SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_ID")

if not SERVICE_ACCOUNT_PATH:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH 환경변수가 없습니다.")

if not SPREADSHEET_ID:
    raise ValueError("GOOGLE_SHEETS_ID 환경변수가 없습니다.")


# --------------------------------------------------
# 값 변환 함수
# --------------------------------------------------

def to_int(value):
    if value in ("", None):
        return None
    return int(float(value))


def to_float(value):
    if value in ("", None):
        return None
    return float(value)


# --------------------------------------------------
# Google Sheets 연결
# --------------------------------------------------

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

google_credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_PATH,
    scopes=scopes,
)

gc = gspread.authorize(google_credentials)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)


# --------------------------------------------------
# 시트 읽기
# --------------------------------------------------

daily_sheet = spreadsheet.worksheet("daily_stats")
gsc_sheet = spreadsheet.worksheet("gsc_daily")

daily_rows = daily_sheet.get_all_records()
gsc_rows = gsc_sheet.get_all_records()


# --------------------------------------------------
# 날짜 기준 Dictionary 변환
# --------------------------------------------------

daily_by_date = {
    str(row["stat_date"]): row
    for row in daily_rows
    if row.get("stat_date")
}

gsc_by_date = {
    str(row["date"]): row
    for row in gsc_rows
    if row.get("date")
}


# --------------------------------------------------
# 두 데이터가 모두 존재하는 날짜만 추출
# --------------------------------------------------

common_dates = sorted(
    set(daily_by_date.keys()) & set(gsc_by_date.keys())
)

documents = []

for date in common_dates:
    daily = daily_by_date[date]
    gsc = gsc_by_date[date]

    pv = to_int(daily.get("pv"))

    document = {
        # 과제 기본 필드
        "date": date,
        "value": pv,
        "memo": str(daily.get("memo", "")),

        # WordPress / GA4 / AdSense
        "posts": to_int(daily.get("posts")),
        "pages": to_int(daily.get("pages")),
        "users": to_int(daily.get("users")),
        "pv": pv,
        "adsense_estimated": to_float(
            daily.get("adsense_estimated")
        ),

        # Google Search Console
        "gsc_type": str(gsc.get("type", "")),
        "gsc_clicks": to_int(gsc.get("clicks")),
        "gsc_impressions": to_int(gsc.get("impressions")),
        "gsc_ctr": to_float(gsc.get("ctr")),
        "gsc_position": to_float(gsc.get("position")),
    }

    documents.append(document)


# --------------------------------------------------
# 데이터 검증 결과 출력
# --------------------------------------------------

print("=" * 60)
print("Google Sheets 데이터 확인")
print("=" * 60)

print(f"daily_stats 행 수 : {len(daily_rows)}")
print(f"gsc_daily 행 수  : {len(gsc_rows)}")
print(f"공통 날짜 수      : {len(common_dates)}")

if common_dates:
    print(
        f"공통 기간         : "
        f"{common_dates[0]} ~ {common_dates[-1]}"
    )

print()

if documents:
    print("첫 번째 변환 데이터:")
    print(documents[0])

    print()
    print("마지막 변환 데이터:")
    print(documents[-1])


# --------------------------------------------------
# 실제 Firestore 저장 여부
# --------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument(
    "--write",
    action="store_true",
    help="Firestore에 실제 데이터를 저장합니다.",
)

args = parser.parse_args()

if not args.write:
    print()
    print(
        "검증 모드입니다. "
        "Firestore에는 아직 저장하지 않았습니다."
    )
    print(
        "문제가 없으면 다음 명령을 실행하세요:"
    )
    print("python import_to_firestore.py --write")
    raise SystemExit


# --------------------------------------------------
# Firebase 연결
# --------------------------------------------------

if not firebase_admin._apps:
    firebase_credential = credentials.Certificate(
        SERVICE_ACCOUNT_PATH
    )
    firebase_admin.initialize_app(firebase_credential)

db = firestore.client()


# --------------------------------------------------
# Firestore Batch 저장
# --------------------------------------------------

batch = db.batch()

for document in documents:
    document_id = document["date"]

    doc_ref = (
        db.collection("data")
        .document(document_id)
    )

    batch.set(
        doc_ref,
        {
            **document,
            "imported_at": firestore.SERVER_TIMESTAMP,
        },
    )

batch.commit()


print()
print("=" * 60)
print("Firestore 저장 완료")
print("=" * 60)
print(f"저장 문서 수: {len(documents)}")
print("컬렉션: data")