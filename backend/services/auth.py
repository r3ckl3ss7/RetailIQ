import os
import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, Response, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User as UserModel
from models.auth import Auth as AuthModel
from schemas.auth import LoginModel, RegisterModel
from middlewares.auth import refresh_token, access_token, verify_token

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
)
REFRESH_TOKEN_TTL = int(os.getenv('REFRESH_TOKEN_TTL', 7 * 24 * 60))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def register_user(db: AsyncSession, payload: RegisterModel):
    result = await db.execute(
        select(UserModel).where(UserModel.email == payload.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = UserModel(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    token = refresh_token(user.id)
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    tkn = AuthModel(
        user_id=user.id,
        token=hashed_token,
    )
    db.add(tkn)
    await db.commit()
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
    }


async def login_user(db: AsyncSession, payload: LoginModel, response: Response):
    result = await db.execute(
        select(UserModel).where(UserModel.email == payload.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    info = {
        "sub": user.email,
        "user_id": user.id,
        "exp": expire,
    }
    
    accessToken = access_token(info)
    refreshToken = refresh_token(user.id)
    
    hashed_token = hashlib.sha256(refreshToken.encode()).hexdigest()
    db_token = AuthModel(
        user_id=user.id,
        token=hashed_token
    )
    db.add(db_token)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=refreshToken,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_TTL * 60,
        path="/auth",
    )

    return {
        "access_token": accessToken,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
        },
    }


async def refresh_access_token(db: AsyncSession, request: Request, response: Response):
    refreshToken = request.cookies.get("refresh_token")
    if not refreshToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    token_data = verify_token(refreshToken)
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token structure",
        )

    hashed_token = hashlib.sha256(refreshToken.encode()).hexdigest()
    result = await db.execute(
        select(AuthModel).where(
            AuthModel.user_id == user_id,
            AuthModel.token == hashed_token
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    user_result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    info = {
        "sub": user.email,
        "user_id": user.id,
        "exp": expire,
    }
    new_access_token = access_token(info)
    
    new_refresh_token = refresh_token(user.id)
    new_hashed_token = hashlib.sha256(new_refresh_token.encode()).hexdigest()
    
    await db.delete(db_token)
    
    new_db_token = AuthModel(
        user_id=user.id,
        token=new_hashed_token
    )
    db.add(new_db_token)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,  
        samesite="lax",
        max_age=REFRESH_TOKEN_TTL * 60,
        path="/auth",
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


async def logout_user(db: AsyncSession, request: Request, response: Response):
    refreshToken = request.cookies.get("refresh_token")
    if refreshToken:
        hashed_token = hashlib.sha256(refreshToken.encode()).hexdigest()
        result = await db.execute(
            select(AuthModel).where(AuthModel.token == hashed_token)
        )
        db_token = result.scalar_one_or_none()
        if db_token:
            await db.delete(db_token)
            await db.commit()
            
    response.delete_cookie("refresh_token", path="/auth")
    
    return {"Message": "Logged out successfully"}
