from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_db
from middlewares.auth import current_user
from schemas.ai import ChatMessageCreate, ChatMessageOut, ChatSessionOut
from services.ai import (
    chat_with_agent,
    get_chat_history,
    list_chat_sessions,
    delete_chat_session,
)

router = APIRouter(
    prefix="/ai",
    tags=["ai"]
)

@router.post("/chat", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
async def chat(
    business_id: int,
    payload: ChatMessageCreate,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Send a message to the AI chatbot, executing a business-isolated database query
    and persisting the chat message and the AI response.
    """
    return await chat_with_agent(
        db=db,
        business_id=business_id,
        user_id=current_user_id,
        message=payload.message,
        session_id=payload.session_id,
    )

@router.get("/history/{session_id}", response_model=list[ChatMessageOut])
async def get_history(
    session_id: str,
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve the message history for a specific chat session of a business.
    """
    # Verify business ownership first
    from services.products import _get_business_for_user
    await _get_business_for_user(db, business_id, current_user_id)
    
    return await get_chat_history(db, business_id, session_id)

@router.get("/sessions", response_model=list[ChatSessionOut])
async def get_sessions(
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all active chat session IDs and metadata for a business.
    """
    # Verify business ownership first
    from services.products import _get_business_for_user
    await _get_business_for_user(db, business_id, current_user_id)
    
    return await list_chat_sessions(db, business_id)

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    business_id: int,
    current_user_id: int = Depends(current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Deletes the conversation history for a specific session.
    """
    # Verify business ownership first
    from services.products import _get_business_for_user
    await _get_business_for_user(db, business_id, current_user_id)
    
    await delete_chat_session(db, business_id, session_id)
