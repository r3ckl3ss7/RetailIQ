import jwt
from pydantic import EmailStr
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os
import uuid
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
)
REFRESH_TOKEN_TTL = int(os.getenv('REFRESH_TOKEN_TTL', 7 * 24 * 60))
from pydantic import BaseModel
bearer_scheme = HTTPBearer(auto_error=False)


def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


async def auth(
    user_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    token_user_id = await current_user(credentials)

    if token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this business",
        )
    return token_user_id


async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    raw_token = credentials.credentials
    if raw_token.lower().startswith("bearer"):
        raw_token = raw_token[6:].lstrip(" ")

    token_data = verify_token(raw_token)
    user_id = token_data.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user_id claim",
        )
    return user_id


class TokenPayload(BaseModel):
    sub: EmailStr
    user_id: int
    exp: float


def refresh_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_TTL)
    refreshToken = jwt.encode(
        {"user_id": user_id, "exp": expire, "jti": str(uuid.uuid4())},
        SECRET_KEY,
        algorithm='HS256'
    )
    
    return refreshToken


def access_token(payload: TokenPayload | dict):
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif hasattr(payload, "dict"):
        data = payload.dict()
    else:
        data = dict(payload)

    if "exp" not in data:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        data["exp"] = expire

    if "jti" not in data:
        data["jti"] = str(uuid.uuid4())

    accessToken = jwt.encode(
        data,
        SECRET_KEY,
        algorithm='HS256'
    )

    return accessToken