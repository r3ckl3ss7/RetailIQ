from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import verify_token

bearer_scheme = HTTPBearer(auto_error=False)


async def auth(
    user_id: int,
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

    if token_data.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this business",
        )
    return token_data.get("user_id")
