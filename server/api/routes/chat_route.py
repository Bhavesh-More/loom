from uuid import UUID
from fastapi import APIRouter, HTTPException

from db.chat import ChatRepository
from db.schema.chat import ChatSessionItem, ChatSessionDetail
from db.database import database

router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
)

chat_repository = ChatRepository(database)

from config.contant import DEV_USER_ID


@router.get("/get-chat/{session_id}", response_model=ChatSessionDetail)
async def get_chat(session_id: UUID):
    """
    Returns the chat session details and its chronological messages.
    """
    conn = await database.get_conn()
    try:
        session = await chat_repository.get_chat_session(conn, str(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        messages = await chat_repository.get_chat_messages(conn, str(session_id))
        return {
            "session": session,
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat session: {str(e)}")
    finally:
        await database.release_conn(conn)


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

