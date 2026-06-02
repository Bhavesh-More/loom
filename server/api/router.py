from fastapi import APIRouter

from api.routes.project_route import router as project_router

router = APIRouter()

router.include_router(project_router)