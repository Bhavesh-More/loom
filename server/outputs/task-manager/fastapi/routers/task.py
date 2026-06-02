from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from models.task import Task
from schemas.task import TaskCreate, TaskUpdate
from supabase_client import get_tasks, create_task, update_task, delete_task

task_router = APIRouter()

@task_router.post("/tasks", response_model=Task)
async def create_task_endpoint(task: TaskCreate):
    """
    Create a new task.

    Args:
    task (TaskCreate): The task to create.

    Returns:
    Task: The created task.
    """
    if task.status not in ['todo', 'in-progress', 'done']:
        raise HTTPException(status_code=400, detail="Invalid status")
    data = create_task(task.title, task.description, task.status)
    return data.data[0]

@task_router.get("/tasks", response_model=List[Task])
async def get_tasks_endpoint():
    """
    Get all tasks.

    Returns:
    List[Task]: The list of tasks.
    """
    data = get_tasks()
    return data.data

@task_router.get("/tasks/{id}", response_model=Task)
async def get_task_endpoint(id: int):
    """
    Get a task by id.

    Args:
    id (int): The id of the task.

    Returns:
    Task: The task.
    """
    data = get_tasks()
    for task in data.data:
        if task['id'] == id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@task_router.put("/tasks/{id}", response_model=Task)
async def update_task_endpoint(id: int, task: TaskUpdate):
    """
    Update a task.

    Args:
    id (int): The id of the task.
    task (TaskUpdate): The updated task.

    Returns:
    Task: The updated task.
    """
    if task.status and task.status not in ['todo', 'in-progress', 'done']:
        raise HTTPException(status_code=400, detail="Invalid status")
    data = update_task(id, task.title, task.description, task.status)
    return data.data[0]

@task_router.delete("/tasks/{id}")
async def delete_task_endpoint(id: int):
    """
    Delete a task.

    Args:
    id (int): The id of the task.

    Returns:
    JSONResponse: A JSON response with a message.
    """
    data = delete_task(id)
    return JSONResponse(content={"message": "Task deleted"}, status_code=200)