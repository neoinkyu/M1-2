import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("CODYSSEY_API_KEY")
base_url = os.getenv("CODYSSEY_BASE_URL")

if not api_key:
    raise ValueError("CODYSSEY_API_KEY 환경변수가 없습니다.")

if not base_url:
    raise ValueError("CODYSSEY_BASE_URL 환경변수가 없습니다.")


client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)


print("=" * 60)
print("Codyssey OpenAI 호환 API 연결 테스트")
print("=" * 60)

models = client.models.list()

for model in models.data:
    print(model.id)

model = os.getenv("CODYSSEY_MODEL")

if not model:
    raise ValueError("CODYSSEY_MODEL 환경변수가 없습니다.")


response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "당신은 간결하게 답변하는 테스트용 AI입니다.",
        },
        {
            "role": "user",
            "content": "연결 테스트입니다. '정상 연결'이라고 답해주세요.",
        },
    ],
    max_tokens=50,
)


print()
print("AI 응답:")
print(response.choices[0].message.content)