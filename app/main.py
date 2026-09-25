from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.firebase import get_firestore_db
from app.routers.data import router as data_router

from app.routers.data import router as data_router
from app.routers.chat import router as chat_router

from app.routers.conversations import (
    router as conversations_router,
)

app = FastAPI(
    title="AuctionSuit AI Assistant API",
    description=(
        "옥션슈트 통계 데이터를 기반으로 동작하는 "
        "AI 비서 API"
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(data_router)
app.include_router(chat_router)
app.include_router(conversations_router)

@app.get("/")
def root():
    return {
        "message": "AuctionSuit AI Assistant API"
    }


@app.get("/health")
def health_check():
    get_firestore_db()

    return {
        "status": "ok",
        "database": "firestore",
        "project": "M1-2",
    }