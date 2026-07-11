from exceptions.user import UserNotFoundException
from schemas.auth import EmailModel
from schemas.auth import OTPModel
from exceptions.user import InvalidOTP
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_async_db
from schemas.auth import LoginModel, RegisterModel, ResetPasswordModel
from services.auth import (
    login_user,
    logout_user,
    register_user,
    refresh_access_token,
    forgot_password as forgot_password_service,
    reset_password as reset_password_service,
)
from services.auth import verify_otp as verify_otp_service
from services.auth import resend_otp as resend_otp_service

from utils.generate_otp import gen_otp


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

@router.post("/verify-otp")
async def verify_otp(
    payload: OTPModel,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    try:
        return await verify_otp_service(db, payload)
    except InvalidOTP as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_code": exc.error_code}
        )

@router.post('/resend-otp')
async def resend_otp(payload:EmailModel,db:AsyncSession=Depends(get_async_db)):
    try:
        return await resend_otp_service(db, payload)
    except UserNotFoundException as exc:
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


@router.post("/forgot-password")
async def forgot_password_route(
    payload: EmailModel,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    try:
        return await forgot_password_service(db, payload)
    except UserNotFoundException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_code": exc.error_code}
        )


@router.post("/reset-password")
async def reset_password_route(
    payload: ResetPasswordModel,
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    try:
        return await reset_password_service(db, payload)
    except UserNotFoundException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_code": exc.error_code}
        )
    except InvalidOTP as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_code": exc.error_code}
        )
