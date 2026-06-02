from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from routers import task_router
from supabase_client import get_tasks, create_task, update_task, delete_task

app = FastAPI()

app.include_router(task_router)