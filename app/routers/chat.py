from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat_api(request: ChatRequest):
    try:
        return chat(
            message=request.message,
            conversation_id=request.conversation_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )