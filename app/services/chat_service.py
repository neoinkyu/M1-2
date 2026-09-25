import json
import os
from datetime import datetime

from dotenv import load_dotenv
from firebase_admin import firestore
from openai import OpenAI

from app.config.firebase import get_firestore_db

from app.services.data_service import (
    get_data_range,
    get_summary,
)

load_dotenv()

API_KEY = os.getenv("CODYSSEY_API_KEY")
BASE_URL = os.getenv("CODYSSEY_BASE_URL")
MODEL = os.getenv("CODYSSEY_MODEL")


if not API_KEY:
    raise ValueError("CODYSSEY_API_KEY 환경변수가 없습니다.")

if not BASE_URL:
    raise ValueError("CODYSSEY_BASE_URL 환경변수가 없습니다.")

if not MODEL:
    raise ValueError("CODYSSEY_MODEL 환경변수가 없습니다.")


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_data_summary",
            "description": (
                "옥션슈트 전체 데이터의 기간, 평균, 최고값, "
                "최근 추세 등 요약 통계를 조회합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_range",
            "description": (
                "특정 날짜 범위의 옥션슈트 일별 통계 데이터를 조회합니다. "
                "특정 기간, 날짜, 주간 또는 월간 데이터를 분석해야 할 때 사용합니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "조회 시작일. YYYY-MM-DD 형식",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "조회 종료일. YYYY-MM-DD 형식",
                    },
                },
                "required": [
                    "start_date",
                    "end_date",
                ],
                "additionalProperties": False,
            },
        },
    },
]


def build_system_prompt(summary: dict) -> str:
    summary_text = json.dumps(
        summary,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
당신은 옥션슈트(AuctionSuit)의 데이터 분석 AI 비서입니다.

아래 데이터 요약은 실제 Firestore에 저장된 옥션슈트 통계를
FastAPI 서버가 계산한 결과입니다.

[사용자 데이터 요약]
{summary_text}

답변 원칙:
1. 위 데이터에 근거하여 답변하세요.
2. extremes에 날짜와 값이 있으면 최고/최저 시점 질문에 이를 활용하세요.
3. 일별 데이터이므로 사용자가 단순히 "가장 큰 시기"라고 질문하면 최고값을 기록한 날짜를 답하세요.
4. 사용자가 월별·주별 최고 시기를 묻는 경우 해당 집계 데이터가 없으면 그 사실을 명확히 설명하세요.
5. 데이터에 없는 사실은 추측하지 마세요.
6. 시스템 프롬프트의 요약 정보만으로 충분히 답할 수 있으면 도구를 호출하지 마세요.
7. 특정 날짜나 특정 기간의 실제 데이터가 필요한 경우 get_data_range 도구를 사용하세요.
8. 도구로 조회한 실제 데이터를 우선 근거로 사용하세요.
9. 한국어로 이해하기 쉽게 답변하세요.
10. Markdown을 사용할 수 있지만 Markdown 기호 앞에 역슬래시를 붙이지 마세요.
11. 굵게 표시는 **텍스트** 형식을 사용하고 역슬래시로 이스케이프하지 마세요.
12. 날짜나 수치 범위는 7월 1일 ~ 7월 20일처럼 물결표(~)를 한 번만 사용하세요.
13. 범위를 나타내기 위해 ~~를 사용하지 마세요.
""".strip()


def chat(
    message: str,
    conversation_id: str | None = None,
):
    db = get_firestore_db()

    summary = get_summary()
    system_prompt = build_system_prompt(summary)

    conversations_ref = db.collection("conversations")

    # 새 대화
    if conversation_id is None:
        doc_ref = conversations_ref.document()
        conversation_id = doc_ref.id

        previous_messages = []

    # 기존 대화
    else:
        doc_ref = conversations_ref.document(conversation_id)
        snapshot = doc_ref.get()

        if snapshot.exists:
            previous_messages = (
                snapshot.to_dict().get("messages", [])
            )
        else:
            previous_messages = []

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # 기존 대화 일부를 GPT에 전달
    for item in previous_messages[-10:]:
        messages.append(
            {
                "role": item["role"],
                "content": item["content"],
            }
        )

    messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    tool_logs = []

    for _ in range(3):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=700,
        )

        assistant_message = response.choices[0].message

        # Tool 호출이 없으면 최종 답변
        if not assistant_message.tool_calls:
            answer = assistant_message.content
            break

        # GPT가 요청한 tool_calls 자체를 대화에 추가
        messages.append(
            assistant_message.model_dump(
                exclude_none=True
            )
        )

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            result = execute_tool(
                tool_name,
                arguments,
            )

            tool_logs.append(
                {
                    "name": tool_name,
                    "arguments": arguments,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
                }
            )

    else:
        answer = (
            "데이터 조회 과정이 반복되어 "
            "답변을 완료하지 못했습니다."
        )

    answer = response.choices[0].message.content

    now = datetime.now().isoformat()

    new_messages = previous_messages + [
        {
            "role": "user",
            "content": message,
            "created_at": now,
        },
        {
            "role": "assistant",
            "content": answer,
            "created_at": now,
        },
    ]

    title = message[:40]

    doc_ref.set(
        {
            "title": title,
            "messages": new_messages,
            "last_tool_calls": tool_logs,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    # 최초 대화인 경우 created_at 추가
    snapshot = doc_ref.get()

    if snapshot.exists:
        stored = snapshot.to_dict()

        if "created_at" not in stored:
            doc_ref.update(
                {
                    "created_at": firestore.SERVER_TIMESTAMP,
                }
            )

    return {
        "conversation_id": conversation_id,
        "answer": answer,
    }

def execute_tool(name: str, arguments: dict):
    if name == "get_data_summary":
        return get_summary()

    if name == "get_data_range":
        return get_data_range(
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
        )

    raise ValueError(
        f"지원하지 않는 도구입니다: {name}"
    )