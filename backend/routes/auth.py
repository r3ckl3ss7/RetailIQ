from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_db
from schemas.auth import LoginModel, RegisterModel, RefreshTokenModel
from services.auth import login_user, logout_user, register_user, refresh_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterModel,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    return await register_user(db, payload)


@router.post("/login")
async def login(
    payload: LoginModel,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    return await login_user(db, payload)


@router.post("/refresh")
async def refresh(
    payload: RefreshTokenModel,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    return await refresh_access_token(db, payload)


@router.post('/logout')
async def logout(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    payload: RefreshTokenModel | None = None,
):
    return await logout_user(db, payload)
