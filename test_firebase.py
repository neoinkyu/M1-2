import os

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore


load_dotenv()

service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

if not service_account_path:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH 환경변수가 없습니다.")

cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred)

db = firestore.client()

print("Firestore 연결 성공!")