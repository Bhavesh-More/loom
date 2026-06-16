from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import router
from context_system.service import context_system
from db.database import database


@asynccontextmanager
async def lifespan(app: FastAPI):
	await database.connect()
	await context_system.startup()
	try:
		yield
	finally:
		await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
