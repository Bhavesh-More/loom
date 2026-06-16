from fastapi import APIRouter

from api.routes.project_route import router as project_router
from api.routes.agent_route import router as agent_router
from api.routes.chat_route import router as chat_router
from api.routes.workspace_route import router as workspace_router
from api.routes.context_route import router as context_router

router = APIRouter()

router.include_router(project_router)
router.include_router(agent_router)
router.include_router(chat_router)
router.include_router(workspace_router)
router.include_router(context_router)
