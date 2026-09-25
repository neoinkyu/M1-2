from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(
        ...,
        pattern="^(user|assistant)$"
    )
    content: str


class ConversationCreate(BaseModel):
    title: str
    messages: list[Message]