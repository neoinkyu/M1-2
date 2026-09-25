from firebase_admin import firestore

from app.config.firebase import get_firestore_db
from app.models.conversation import ConversationCreate


COLLECTION_NAME = "conversations"


def create_conversation(data: ConversationCreate):
    db = get_firestore_db()

    doc_ref = db.collection(COLLECTION_NAME).document()

    messages = [
        message.model_dump()
        for message in data.messages
    ]

    document = {
        "title": data.title,
        "messages": messages,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    doc_ref.set(document)

    return {
        "id": doc_ref.id,
        "title": data.title,
        "messages": messages,
    }


def get_conversations():
    db = get_firestore_db()

    docs = (
        db.collection(COLLECTION_NAME)
        .order_by(
            "updated_at",
            direction=firestore.Query.DESCENDING,
        )
        .stream()
    )

    conversations = []

    for doc in docs:
        data = doc.to_dict()

        conversations.append(
            {
                "id": doc.id,
                "title": data.get(
                    "title",
                    "제목 없음"
                ),
                "created_at": data.get(
                    "created_at"
                ),
                "updated_at": data.get(
                    "updated_at"
                ),
                "message_count": len(
                    data.get("messages", [])
                ),
            }
        )

    return conversations


def get_conversation(document_id: str):
    db = get_firestore_db()

    doc_ref = (
        db.collection(COLLECTION_NAME)
        .document(document_id)
    )

    snapshot = doc_ref.get()

    if not snapshot.exists:
        raise LookupError(
            f"{document_id} 대화를 찾을 수 없습니다."
        )

    data = snapshot.to_dict()

    return {
        "id": snapshot.id,
        **data,
    }


def delete_conversation(document_id: str):
    db = get_firestore_db()

    doc_ref = (
        db.collection(COLLECTION_NAME)
        .document(document_id)
    )

    snapshot = doc_ref.get()

    if not snapshot.exists:
        raise LookupError(
            f"{document_id} 대화를 찾을 수 없습니다."
        )

    doc_ref.delete()

    return {
        "id": document_id,
        "message": "대화 기록이 삭제되었습니다.",
    }