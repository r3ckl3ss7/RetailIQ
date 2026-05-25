from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.auth import LoginModel, RegisterModel
from services.auth import login_user, logout_user, register_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterModel,
    db: Annotated[Session, Depends(get_db)],
):
    return register_user(db, payload)


@router.post("/login")
def login(
    payload: LoginModel,
    db: Annotated[Session, Depends(get_db)],
):
    return login_user(db, payload)


@router.post('/logout')
def logout():
    return logout_user()
