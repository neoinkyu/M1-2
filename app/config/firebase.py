import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore


load_dotenv()


def get_firestore_db():

    if not firebase_admin._apps:

        # ------------------------------------------
        # Render 등 배포 환경
        # ------------------------------------------

        service_account_json = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT_JSON"
        )

        if service_account_json:

            try:
                service_account_info = json.loads(
                    service_account_json
                )

            except json.JSONDecodeError as e:
                raise ValueError(
                    "FIREBASE_SERVICE_ACCOUNT_JSON이 "
                    "올바른 JSON 형식이 아닙니다."
                ) from e

            cred = credentials.Certificate(
                service_account_info
            )

        else:

            # ------------------------------------------
            # 로컬 개발 환경
            # ------------------------------------------

            service_account_path = os.getenv(
                "FIREBASE_SERVICE_ACCOUNT_PATH"
            )

            if not service_account_path:
                raise ValueError(
                    "Firebase 서비스 계정 정보가 없습니다. "
                    "FIREBASE_SERVICE_ACCOUNT_JSON 또는 "
                    "FIREBASE_SERVICE_ACCOUNT_PATH를 설정하세요."
                )

            cred = credentials.Certificate(
                service_account_path
            )

        firebase_admin.initialize_app(
            cred
        )

    return firestore.client()