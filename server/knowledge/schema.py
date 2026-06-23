from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class KnowledgeEntry(BaseModel):
    id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)
    timestamp: datetime
    source_agent: str = Field(..., min_length=1)
    priority: Literal["low", "medium", "high"]
    tags: list[str] = Field(default_factory=list)
