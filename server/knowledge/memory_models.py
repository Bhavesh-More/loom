from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class AgentMemoryEntry(BaseModel):
    id: Optional[UUID] = None
    agent_id: str = Field(..., min_length=1)
    context: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    learned_info: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None


class AgentExecutionEntry(BaseModel):
    id: Optional[UUID] = None
    agent_id: str = Field(..., min_length=1)
    task_id: str = Field(..., min_length=1)
    input_data: str = Field(..., min_length=1)
    output_data: str = Field(..., min_length=1)
    status: Literal["success", "failure"]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

class AgentDecisionEntry(BaseModel):
    id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    agent_id: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    reasoning: str = Field(..., min_length=1)
    outcome: str = Field(..., min_length=1)
    created_at: Optional[datetime] = None
