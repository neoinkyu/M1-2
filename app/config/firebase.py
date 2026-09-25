import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore


load_dotenv()


def get_firestore_db():
    if not firebase_admin._apps:
        service_account_path = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT_PATH"
        )

        if not service_account_path:
            raise ValueError(
                "FIREBASE_SERVICE_ACCOUNT_PATH 환경변수가 없습니다."
            )

        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()