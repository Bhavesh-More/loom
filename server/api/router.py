from fastapi import APIRouter

from api.routes.project_route import router as project_router
from api.routes.agent_route import router as agent_router

router = APIRouter()

router.include_router(project_router)
router.include_router(agent_router)