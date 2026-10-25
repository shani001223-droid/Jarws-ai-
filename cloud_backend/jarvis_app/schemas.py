"""Validated API request/response models."""
from typing import Optional
from pydantic import BaseModel, Field

class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    locale: Optional[str] = Field(default="en", max_length=32)
    conversation_id: Optional[str] = Field(default=None, min_length=36, max_length=64)

class AssistantResponse(BaseModel):
    reply: str
    mode: str = "gemini"
