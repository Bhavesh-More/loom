from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Any, Dict, List, Optional
from knowledge.memory_service import memory_service
from knowledge.memory_models import AgentMemoryEntry, AgentExecutionEntry, AgentDecisionEntry
from dependencies.auth_dep import get_current_user

router = APIRouter(
    prefix="/knowledge",
    tags=["memory"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/memory/add", response_model=AgentMemoryEntry)
async def add_memory(entry: AgentMemoryEntry):
    try:
        return await memory_service.save_memory(entry)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save memory: {e}"
        )

@router.get("/memory/get", response_model=List[AgentMemoryEntry])
async def get_memories(
    agent_id: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None)
):
    return await memory_service.get_memories(agent_id=agent_id, tags=tags)

@router.post("/execution/add", response_model=AgentExecutionEntry)
async def add_execution(entry: AgentExecutionEntry):
    try:
        return await memory_service.save_execution(entry)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save execution: {e}"
        )

@router.get("/execution/get", response_model=List[AgentExecutionEntry])
async def get_executions(
    agent_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None)
):
    return await memory_service.get_executions(agent_id=agent_id, status=status, task_id=task_id)

@router.post("/decision/add", response_model=AgentDecisionEntry)
async def add_decision(entry: AgentDecisionEntry):
    try:
        return await memory_service.save_decision(entry)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save decision: {e}"
        )

@router.get("/historical-context")
async def get_historical_context(
    agent_id: str = Query(...),
    task: str = Query(...),
    tags: Optional[List[str]] = Query(None)
):
    try:
        return await memory_service.get_historical_context(agent_id=agent_id, task=task, tags=tags)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve historical context: {e}"
        )


@router.get("/memory/semantic-search")
async def semantic_search_memories(
    query: str = Query(...),
    agent_id: Optional[str] = Query(None),
    limit: int = Query(5)
):
    try:
        results = await memory_service.semantic_search_memories(query, agent_id=agent_id, limit=limit)
        return [
            {
                "memory": memory,
                "similarity_score": score
            }
            for memory, score in results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {e}"
        )
