from pydantic import BaseModel, EmailStr
from datetime import datetime


class User(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    email: EmailStr
    created_at: datetime


class Business(BaseModel):
    model_config = {"from_attributes": True}
