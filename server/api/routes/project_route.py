from uuid import UUID

from fastapi import APIRouter, HTTPException

from db.schema.project import CreateProjectRequest, CreateProjectResponse
from dependencies.project_dep import project_service

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.post("", response_model=CreateProjectResponse)
async def create_project(request: CreateProjectRequest):
    return await project_service.create_project(
        name=request.name,
        description=request.description,
        agent_ids=[str(agent_id) for agent_id in request.agent_ids]
    )


@router.get("/{project_id}")
async def get_project(project_id: UUID):
    project = await project_service.get_project(str(project_id))

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return project