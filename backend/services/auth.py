from schemas.auth import EmailModel
from utils.send_otp import send_mail
from sqlalchemy import update
from exceptions.user import InvalidOTP
from exceptions.user import UserNotFoundException
from schemas.auth import OTPModel
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
from schemas.auth import LoginModel, RegisterModel, ResetPasswordModel
from middlewares.auth import refresh_token, access_token, verify_token

from utils.generate_otp import gen_otp
from redis_client import redisClient

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


from exceptions.user import EmailAlreadyRegisteredException


async def register_user(db: AsyncSession, payload: RegisterModel):
    result = await db.execute(
        select(UserModel).where(UserModel.email == payload.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise EmailAlreadyRegisteredException()
    otp=gen_otp()
    try:
        redisClient.set(f"otp:{payload.email}", str(otp), ex=900)
    except Exception as e:
        print(f"Redis error during registration: {e}")

    user = UserModel(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        otp=otp,
        is_verified=False,
        otp_timestamp=datetime.now(timezone.utc)
    )
    await send_mail(payload={
        "email":user.email,
        "otp":otp
    })
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "message":"OTP Sent to your email successfully"
    }


async def resend_otp(db:AsyncSession,payload:EmailModel):
    result=await db.execute(select(UserModel).where(UserModel.email==payload.email))
    user=result.scalar_one_or_none()
    if not user:
        raise UserNotFoundException()
    otp=gen_otp()
    try:
        redisClient.set(f"otp:{payload.email}", str(otp), ex=900)
    except Exception as e:
        print(f"Redis error during resend: {e}")
    
    user.otp = otp
    user.otp_timestamp = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(user)
    await send_mail(payload={
        "email":user.email,
        "otp":otp
    })
    return {
        "success":True,
        "Message":"OTP Resent to your email successfully"
    }
async def verify_otp(db:AsyncSession,payload=OTPModel):
    result=await db.execute(select(UserModel).where(UserModel.email==payload.email))
    user=result.scalar_one_or_none()
    if not user:
        raise UserNotFoundException()
    
    redis_otp = None
    try:
        redis_otp = redisClient.get(f"otp:{payload.email}")
        if isinstance(redis_otp, bytes):
            redis_otp = redis_otp.decode('utf-8')
    except Exception as e:
        print(f"Redis error during verification lookup: {e}")

    if redis_otp is not None:
        if int(redis_otp) != payload.otp:
            raise InvalidOTP()
        try:
            redisClient.delete(f"otp:{payload.email}")
        except Exception as e:
            print(f"Redis error deleting OTP: {e}")
    else:
        if payload.otp!=user.otp:
            raise InvalidOTP()
        
        otp_ts=user.otp_timestamp
        if not otp_ts:
            raise InvalidOTP(message="OTP has not been requested or is invalid.")
        
        now = datetime.now(timezone.utc)
        if otp_ts.tzinfo is None:
            otp_ts = otp_ts.replace(tzinfo=timezone.utc)
            
        if now - otp_ts > timedelta(minutes=15):
            raise InvalidOTP(message="OTP has expired. Please request a new one.")
        
    user.is_verified = True
    
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
        "success":True,
        "Message":"OTP verified successfully"
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


async def forgot_password(db: AsyncSession, payload: EmailModel):
    result = await db.execute(
        select(UserModel).where(UserModel.email == payload.email)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundException()
    
    otp = gen_otp()
    try:
        redisClient.set(f"reset_otp:{payload.email}", str(otp), ex=900)
    except Exception as e:
        print(f"Redis error during forgot password: {e}")
        user.otp = otp
        user.otp_timestamp = datetime.now(timezone.utc)
        await db.commit()
        
    await send_mail(payload={
        "email": user.email,
        "otp": otp
    })
    
    return {
        "success": True,
        "Message": "OTP sent to your email successfully"
    }


async def reset_password(db: AsyncSession, payload: ResetPasswordModel):
    result = await db.execute(
        select(UserModel).where(UserModel.email == payload.email)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundException()
    
    redis_otp = None
    try:
        redis_otp = redisClient.get(f"reset_otp:{payload.email}")
        if isinstance(redis_otp, bytes):
            redis_otp = redis_otp.decode('utf-8')
    except Exception as e:
        print(f"Redis error during reset verification: {e}")
        
    if redis_otp is not None:
        if int(redis_otp) != payload.otp:
            raise InvalidOTP()
        try:
            redisClient.delete(f"reset_otp:{payload.email}")
        except Exception as e:
            print(f"Redis error deleting reset OTP: {e}")
    else:
        if payload.otp != user.otp:
            raise InvalidOTP()
        
        otp_ts = user.otp_timestamp
        if not otp_ts:
            raise InvalidOTP(message="OTP has not been requested or is invalid.")
        
        now = datetime.now(timezone.utc)
        if otp_ts.tzinfo is None:
            otp_ts = otp_ts.replace(tzinfo=timezone.utc)
            
        if now - otp_ts > timedelta(minutes=15):
            raise InvalidOTP(message="OTP has expired. Please request a new one.")
            
    user.password = hash_password(payload.new_password)
    user.otp = None
    user.otp_timestamp = None
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "Message": "Password reset successfully"
    }
