from pydantic import BaseModel, Field, EmailStr
from typing import Annotated



class RegisterModel(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=100)]
    email: EmailStr
    password: Annotated[str, Field(min_length=6)]


class LoginModel(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenModel(BaseModel):
    refresh_token: str

