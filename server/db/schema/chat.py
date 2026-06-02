from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


from typing import Any


class ChatSessionItem(BaseModel):
    id: UUID
    title: str
    project_id: UUID
    created_at: datetime
    updated_at: datetime


class ChatMessageItem(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    message_type: str
    content: Any
    created_at: datetime


class ChatSessionDetail(BaseModel):
    session: ChatSessionItem
    messages: list[ChatMessageItem]

