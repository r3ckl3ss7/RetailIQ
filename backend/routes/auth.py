from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_db
from schemas.auth import LoginModel, RegisterModel
from services.auth import login_user, logout_user, register_user, refresh_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


from exceptions.user import EmailAlreadyRegisteredException


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterModel,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    try:
        return await register_user(db, payload)
    except EmailAlreadyRegisteredException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_code": exc.error_code}
        )


@router.post("/login")
async def login(
    payload: LoginModel,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    return await login_user(db, payload, response)


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    return await refresh_access_token(db, request, response)


@router.post('/logout')
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    return await logout_user(db, request, response)
