import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("CODYSSEY_API_KEY")
base_url = os.getenv("CODYSSEY_BASE_URL")
model = os.getenv("CODYSSEY_MODEL")

if not api_key:
    raise ValueError("CODYSSEY_API_KEY 환경변수가 없습니다.")

if not base_url:
    raise ValueError("CODYSSEY_BASE_URL 환경변수가 없습니다.")

if not model:
    raise ValueError("CODYSSEY_MODEL 환경변수가 없습니다.")


client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "특정 도시의 현재 날씨를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "조회할 도시 이름",
                    }
                },
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]


print("=" * 60)
print("Codyssey Function Calling 지원 테스트")
print(f"모델: {model}")
print("=" * 60)


response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": (
                "사용자의 질문에 답하기 위해 필요한 경우 "
                "제공된 도구를 사용하세요."
            ),
        },
        {
            "role": "user",
            "content": (
                "서울의 현재 날씨를 알려줘. "
                "현재 날씨 정보는 직접 추측하지 말고 "
                "반드시 제공된 도구를 사용해."
            ),
        },
    ],
    tools=tools,
    tool_choice="auto",
    max_tokens=200,
)


message = response.choices[0].message

print()
print("finish_reason:")
print(response.choices[0].finish_reason)

print()
print("content:")
print(message.content)

print()
print("tool_calls:")
print(message.tool_calls)


if message.tool_calls:
    print()
    print("=" * 60)
    print("Function Calling 지원 확인")
    print("=" * 60)

    for tool_call in message.tool_calls:
        print(f"도구 이름: {tool_call.function.name}")
        print(f"도구 인자: {tool_call.function.arguments}")

else:
    print()
    print("=" * 60)
    print("tool_calls가 반환되지 않았습니다.")
    print("=" * 60)