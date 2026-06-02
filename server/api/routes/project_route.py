from fastapi import APIRouter

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.post("")
async def create_project():
    pass


@router.get("/{project_id}")
async def get_project():
    pass