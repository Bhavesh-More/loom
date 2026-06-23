from fastapi import APIRouter, HTTPException, status
from typing import Any, Dict, List
from knowledge.sync_manager import sync_manager
from knowledge.schema import KnowledgeEntry

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/add")
async def add_knowledge(entry: Dict[str, Any]):
    res = await sync_manager.add_knowledge(entry)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res
        )
    return res

@router.get("/get", response_model=List[KnowledgeEntry])
async def get_knowledge():
    return await sync_manager.get_all()

@router.get("/tags/{tag}", response_model=List[KnowledgeEntry])
async def get_knowledge_by_tag(tag: str):
    return await sync_manager.get_by_tag(tag)
