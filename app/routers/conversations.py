from fastapi import APIRouter, HTTPException

from app.models.conversation import ConversationCreate
from app.services import conversation_service


router = APIRouter(
    prefix="/api/conversations",
    tags=["Conversations"],
)


@router.post("")
def create_conversation(
    data: ConversationCreate,
):
    return conversation_service.create_conversation(
        data
    )


@router.get("")
def get_conversations():
    return conversation_service.get_conversations()


@router.get("/{document_id}")
def get_conversation(document_id: str):
    try:
        return conversation_service.get_conversation(
            document_id
        )

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.delete("/{document_id}")
def delete_conversation(document_id: str):
    try:
        return conversation_service.delete_conversation(
            document_id
        )

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )