from fastapi import APIRouter, HTTPException

from db.chat import ChatRepository
from db.schema.chat import ChatSessionItem
from db.database import database

router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
)

chat_repository = ChatRepository(database)

from config.contant import DEV_USER_ID


@router.post("/get-chats", response_model=list[ChatSessionItem])
async def get_chats():
    """
    Returns all chat sessions (id + title) for the current user,
    joined across all their projects, ordered by most recently updated.
    """
    conn = await database.get_conn()
    try:
        chats = await chat_repository.get_chats_by_user(conn, DEV_USER_ID)
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chats: {str(e)}")
    finally:
        await database.release_conn(conn)

