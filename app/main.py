import os

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp.server.transport_security import (
    TransportSecuritySettings,
)

from app.config.firebase import (
    get_firestore_db,
)

from app.mcp_server import mcp

from app.routers.chat import (
    router as chat_router,
)

from app.routers.conversations import (
    router as conversations_router,
)

from app.routers.data import (
    router as data_router,
)


# ==================================================
# 환경변수
# ==================================================

load_dotenv()


def parse_origins():
    value = os.getenv(
        "ALLOWED_ORIGINS",
        (
            "http://127.0.0.1:5500,"
            "http://localhost:5500,"
            "https://m1-2-auctionsuit-ai.vercel.app"
        ),
    )

    return [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ]


ALLOWED_ORIGINS = parse_origins()


# ==================================================
# MCP 보안 설정
# ==================================================

mcp_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,

    allowed_hosts=[
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",

        "m1-2-auctionsuit-ai.onrender.com",
        "m1-2-auctionsuit-ai.onrender.com:*",
    ],

    allowed_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",

        "https://m1-2-auctionsuit-ai.vercel.app",
    ],
)


# ==================================================
# MCP Streamable HTTP 앱
# ==================================================

# streamable_http_path="/" 로 설정해야
# FastAPI의 /mcp mount와 합쳐져서
# 최종 주소가 /mcp가 됩니다.
#
# 기본값 /mcp를 그대로 사용하면
# /mcp/mcp가 되어버립니다.

mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/",
    transport_security=mcp_security,
)


# ==================================================
# FastAPI lifespan
# ==================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:

    # FastAPI에 MCP 앱을 mount하면
    # MCP 하위 앱의 lifespan은 자동 실행되지 않습니다.
    #
    # 따라서 부모 FastAPI가
    # MCP session manager를 직접 실행해야 합니다.

    async with mcp.session_manager.run():

        yield


# ==================================================
# FastAPI
# ==================================================

app = FastAPI(
    title="AuctionSuit AI Assistant API",

    description=(
        "옥션슈트 통계 데이터를 기반으로 "
        "분석·대화·MCP 도구 호출 기능을 제공하는 API"
    ),

    version="1.0.0",

    lifespan=lifespan,
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=ALLOWED_ORIGINS,

    allow_credentials=False,

    allow_methods=[
        "*",
    ],

    # MCP는 일반 API보다
    # 추가 헤더를 사용하므로
    # 전체 허용으로 설정합니다.
    allow_headers=[
        "*",
    ],

    # MCP legacy/session 방식 클라이언트가
    # 세션 ID를 읽을 수 있도록 노출합니다.
    expose_headers=[
        "Mcp-Session-Id",
    ],
)


# ==================================================
# 기존 API Router
# ==================================================

app.include_router(
    data_router
)

app.include_router(
    chat_router
)

app.include_router(
    conversations_router
)


# ==================================================
# 기본 API
# ==================================================

@app.get("/")
def root():

    return {
        "message":
            "AuctionSuit AI Assistant API"
    }


@app.get("/health")
def health_check():

    get_firestore_db()

    return {
        "status": "ok",
        "database": "firestore",
        "project": "M1-2",
        "mcp": "/mcp",
    }


# ==================================================
# MCP
# ==================================================

app.mount(
    "/mcp",
    mcp_http_app,
)