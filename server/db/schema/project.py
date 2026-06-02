from uuid import UUID

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    agent_ids: list[UUID]


class CreateProjectResponse(BaseModel):
    project_id: UUID
    name: str
    description: str | None
    status: str