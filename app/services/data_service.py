from statistics import mean

from firebase_admin import firestore

from app.config.firebase import get_firestore_db
from app.models.data import DataCreate, DataUpdate


COLLECTION_NAME = "data"


# ==================================================
# 데이터 생성
# ==================================================

def create_data(data: DataCreate):
    db = get_firestore_db()

    document_id = data.date.isoformat()

    doc_ref = (
        db.collection(COLLECTION_NAME)
        .document(document_id)
    )

    # 같은 날짜 데이터 중복 방지
    if doc_ref.get().exists:
        raise ValueError(
            f"{document_id} 데이터가 이미 존재합니다."
        )

    document = data.model_dump()

    # Firestore에는 날짜를 문자열로 저장
    document["date"] = document_id

    document["created_at"] = (
        firestore.SERVER_TIMESTAMP
    )

    document["updated_at"] = (
        firestore.SERVER_TIMESTAMP
    )

    doc_ref.set(document)

    return {
        "id": document_id,
        **data.model_dump(
            mode="json"
        ),
    }


# ==================================================
# 전체 데이터 조회
# ==================================================

def get_all_data():
    db = get_firestore_db()

    docs = (
        db.collection(COLLECTION_NAME)
        .order_by("date")
        .stream()
    )

    result = []

    for doc in docs:
        data = doc.to_dict()

        result.append(
            {
                "id": doc.id,
                **data,
            }
        )

    return result


# ==================================================
# 데이터 수정
# ==================================================

def update_data(
    document_id: str,
    data: DataUpdate,
):
    db = get_firestore_db()

    doc_ref = (
        db.collection(COLLECTION_NAME)
        .document(document_id)
    )

    snapshot = doc_ref.get()

    if not snapshot.exists:
        raise LookupError(
            f"{document_id} 데이터를 찾을 수 없습니다."
        )

    update_values = data.model_dump(
        exclude_unset=True
    )

    if not update_values:
        raise ValueError(
            "수정할 데이터가 없습니다."
        )

    update_values["updated_at"] = (
        firestore.SERVER_TIMESTAMP
    )

    doc_ref.update(
        update_values
    )

    updated = (
        doc_ref
        .get()
        .to_dict()
    )

    return {
        "id": document_id,
        **updated,
    }


# ==================================================
# 데이터 삭제
# ==================================================

def delete_data(document_id: str):
    db = get_firestore_db()

    doc_ref = (
        db.collection(COLLECTION_NAME)
        .document(document_id)
    )

    snapshot = doc_ref.get()

    if not snapshot.exists:
        raise LookupError(
            f"{document_id} 데이터를 찾을 수 없습니다."
        )

    doc_ref.delete()

    return {
        "id": document_id,
        "message": "삭제되었습니다.",
    }


# ==================================================
# 통계 공통 함수
# ==================================================

def _clean_numeric_values(values):
    """
    숫자형 데이터만 추출합니다.
    None, 문자열 등은 제외합니다.
    """

    return [
        value
        for value in values
        if isinstance(
            value,
            (int, float)
        )
    ]


def _average(values):
    """
    평균값 계산
    """

    clean_values = (
        _clean_numeric_values(values)
    )

    if not clean_values:
        return None

    return round(
        mean(clean_values),
        4,
    )


def _trend(values):
    """
    최근 7일 평균과
    이전 7일 평균을 비교하여
    상승 / 하락 / 유지 판단

    ±3% 이내는 유지로 판단
    """

    clean_values = (
        _clean_numeric_values(values)
    )

    if len(clean_values) < 14:
        return "판단 불가"

    previous = mean(
        clean_values[-14:-7]
    )

    recent = mean(
        clean_values[-7:]
    )

    if previous == 0:
        return "판단 불가"

    change_rate = (
        (recent - previous)
        / previous
    )

    if change_rate > 0.03:
        return "상승"

    if change_rate < -0.03:
        return "하락"

    return "유지"


def _change_rate(values):
    """
    최근 7일 평균이
    이전 7일 평균보다
    몇 % 증감했는지 계산
    """

    clean_values = (
        _clean_numeric_values(values)
    )

    if len(clean_values) < 14:
        return None

    previous = mean(
        clean_values[-14:-7]
    )

    recent = mean(
        clean_values[-7:]
    )

    if previous == 0:
        return None

    change_rate = (
        (recent - previous)
        / previous
        * 100
    )

    return round(
        change_rate,
        2,
    )


def _extreme_with_date(
    data_list,
    key,
    mode="max",
):
    """
    특정 지표의 최고값 또는 최저값과
    해당 날짜를 함께 반환합니다.
    """

    candidates = [
        row
        for row in data_list
        if isinstance(
            row.get(key),
            (int, float)
        )
    ]

    if not candidates:
        return {
            "date": None,
            "value": None,
        }

    if mode == "min":

        target = min(
            candidates,
            key=lambda row: row[key],
        )

    else:

        target = max(
            candidates,
            key=lambda row: row[key],
        )

    return {
        "date": target.get("date"),
        "value": target.get(key),
    }


# ==================================================
# 특정 기간 데이터 조회
# Function Calling용
# ==================================================

def get_data_range(
    start_date: str,
    end_date: str,
):
    """
    특정 날짜 범위의 일별 데이터를 반환합니다.

    GPT Function Calling에서
    특정 기간 분석이 필요할 때 사용합니다.
    """

    data_list = get_all_data()

    filtered = [
        row
        for row in data_list
        if (
            start_date
            <= row.get(
                "date",
                "",
            )
            <= end_date
        )
    ]

    return [
        {
            "date": row.get(
                "date"
            ),

            "value": row.get(
                "value"
            ),

            "users": row.get(
                "users"
            ),

            "pv": row.get(
                "pv"
            ),

            "adsense_estimated": (
                row.get(
                    "adsense_estimated"
                )
            ),

            "gsc_clicks": row.get(
                "gsc_clicks"
            ),

            "gsc_impressions": (
                row.get(
                    "gsc_impressions"
                )
            ),

            "gsc_ctr": row.get(
                "gsc_ctr"
            ),

            "gsc_position": row.get(
                "gsc_position"
            ),

            "memo": row.get(
                "memo"
            ),
        }

        for row in filtered
    ]


# ==================================================
# 데이터 요약
# ==================================================

def get_summary():
    data_list = get_all_data()

    # 데이터가 하나도 없는 경우
    if not data_list:
        return {
            "period": None,
            "count": 0,

            "metrics": {},

            "extremes": {},

            "trend": {},

            "comparison": {},
        }


    # --------------------------------------------------
    # 지표별 값 추출
    # --------------------------------------------------

    pv_values = [
        row.get("pv")
        for row in data_list
    ]


    user_values = [
        row.get("users")
        for row in data_list
    ]


    click_values = [
        row.get("gsc_clicks")
        for row in data_list
    ]


    impression_values = [
        row.get(
            "gsc_impressions"
        )
        for row in data_list
    ]


    ctr_values = [
        row.get("gsc_ctr")
        for row in data_list
    ]


    position_values = [
        row.get("gsc_position")
        for row in data_list
    ]


    adsense_values = [
        row.get(
            "adsense_estimated"
        )
        for row in data_list
    ]


    # --------------------------------------------------
    # 숫자 데이터 정리
    # --------------------------------------------------

    clean_pv = (
        _clean_numeric_values(
            pv_values
        )
    )


    clean_adsense = (
        _clean_numeric_values(
            adsense_values
        )
    )


    # --------------------------------------------------
    # 최종 Summary 반환
    # --------------------------------------------------

    return {

        # ----------------------------------------------
        # 데이터 기간
        # ----------------------------------------------

        "period": {
            "start":
                data_list[0][
                    "date"
                ],

            "end":
                data_list[-1][
                    "date"
                ],
        },


        # ----------------------------------------------
        # 데이터 개수
        # ----------------------------------------------

        "count":
            len(data_list),


        # ----------------------------------------------
        # 기본 통계
        # ----------------------------------------------

        "metrics": {

            "average_users":
                _average(
                    user_values
                ),


            "average_pv":
                _average(
                    pv_values
                ),


            "max_pv":
                max(
                    clean_pv
                )
                if clean_pv
                else None,


            "min_pv":
                min(
                    clean_pv
                )
                if clean_pv
                else None,


            "average_clicks":
                _average(
                    click_values
                ),


            "average_impressions":
                _average(
                    impression_values
                ),


            "average_ctr":
                _average(
                    ctr_values
                ),


            "average_position":
                _average(
                    position_values
                ),


            "average_adsense":
                _average(
                    adsense_values
                ),


            "total_adsense":
                round(
                    sum(
                        clean_adsense
                    ),
                    4,
                ),
        },


        # ----------------------------------------------
        # 최고 / 최저 시점
        # ----------------------------------------------

        "extremes": {

            "max_users":
                _extreme_with_date(
                    data_list,
                    "users",
                ),


            "max_pv":
                _extreme_with_date(
                    data_list,
                    "pv",
                ),


            "min_pv":
                _extreme_with_date(
                    data_list,
                    "pv",
                    mode="min",
                ),


            "max_adsense":
                _extreme_with_date(
                    data_list,
                    "adsense_estimated",
                ),


            "max_gsc_clicks":
                _extreme_with_date(
                    data_list,
                    "gsc_clicks",
                ),


            "max_gsc_impressions":
                _extreme_with_date(
                    data_list,
                    "gsc_impressions",
                ),


            "max_gsc_ctr":
                _extreme_with_date(
                    data_list,
                    "gsc_ctr",
                ),
        },


        # ----------------------------------------------
        # 최근 추세
        # ----------------------------------------------

        "trend": {

            "pv":
                _trend(
                    pv_values
                ),


            "users":
                _trend(
                    user_values
                ),


            "gsc_clicks":
                _trend(
                    click_values
                ),


            "gsc_impressions":
                _trend(
                    impression_values
                ),


            "gsc_ctr":
                _trend(
                    ctr_values
                ),
        },


        # ----------------------------------------------
        # 최근 7일 vs 이전 7일 증감률
        # 보너스 과제 추가 통계
        # ----------------------------------------------

        "comparison": {

            "pv_change_rate":
                _change_rate(
                    pv_values
                ),


            "users_change_rate":
                _change_rate(
                    user_values
                ),


            "clicks_change_rate":
                _change_rate(
                    click_values
                ),


            "impressions_change_rate":
                _change_rate(
                    impression_values
                ),


            "ctr_change_rate":
                _change_rate(
                    ctr_values
                ),
        },
    }