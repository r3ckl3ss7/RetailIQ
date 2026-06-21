import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User as UserModel
from models.auth import Auth as AuthModel
from schemas.auth import LoginModel, RegisterModel, RefreshTokenModel
from middlewares.auth import refresh_token, access_token, verify_token

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
)

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
    tkn = AuthModel(
        user_id=user.id,
        token=token,
    )
    db.add(tkn)
    await db.commit()
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at,
    }


async def login_user(db: AsyncSession, payload: LoginModel):
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
    
    # Store refresh token in database
    db_token = AuthModel(
        user_id=user.id,
        token=refreshToken
    )
    db.add(db_token)
    await db.commit()

    return {
        "access_token": accessToken,
        "refresh_token": refreshToken,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        },
    }


async def refresh_access_token(db: AsyncSession, payload: RefreshTokenModel):
    # Verify signature and expiration of the refresh token
    token_data = verify_token(payload.refresh_token)
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token structure",
        )

    # Verify presence in database
    result = await db.execute(
        select(AuthModel).where(
            AuthModel.user_id == user_id,
            AuthModel.token == payload.refresh_token
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    # Fetch user details to generate access token
    user_result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Generate new access token
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    info = {
        "sub": user.email,
        "user_id": user.id,
        "exp": expire,
    }
    new_access_token = access_token(info)
    
    # Rotate refresh token: generate new one and delete the old one
    new_refresh_token = refresh_token(user.id)
    await db.delete(db_token)
    
    # Save the new refresh token to DB
    new_db_token = AuthModel(
        user_id=user.id,
        token=new_refresh_token
    )
    db.add(new_db_token)
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


async def logout_user(db: AsyncSession, payload: RefreshTokenModel | None = None):
    if payload and payload.refresh_token:
        result = await db.execute(
            select(AuthModel).where(AuthModel.token == payload.refresh_token)
        )
        db_token = result.scalar_one_or_none()
        if db_token:
            await db.delete(db_token)
            await db.commit()
    return {"Message": "Logged out successfully"}
