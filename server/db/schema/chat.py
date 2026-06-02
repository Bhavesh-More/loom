from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class ChatSessionItem(BaseModel):
    id: UUID
    title: str
    project_id: UUID
    created_at: datetime
    updated_at: datetime
