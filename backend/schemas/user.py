from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class Business(BaseModel):
    model_config = {"from_attributes": True}

    id: int | None = None
    name: str
    gst_number: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    logo_url: str | None = None
    invoice_prefix: str | None = None
    currency: str | None = None
    timezone: str | None = None
    created_at: datetime | None = None


class User(BaseModel):
    model_config = {"from_attributes": True}

    id:int  
    name: str
    email: EmailStr
    avatar_url: str | None = None
    created_at: datetime
    businesses: list[Business] = []



class UpdatedBusiness(BaseModel):
    model_config = {"from_attributes": True}

    name: str | None = Field(None, min_length=1, pattern=r"^\s*\S.*$")
    gst_number: str | None = Field(None, pattern=r"^[a-zA-Z0-9]{15}$")
    phone: str | None = Field(None, pattern=r"^\+?[0-9\s\-]{7,15}$")
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = Field(None, pattern=r"^[a-zA-Z0-9\s\-]{3,10}$")
    logo_url: str | None = None
    invoice_prefix: str | None = None
    currency: str | None = None
    timezone: str | None = None


class UpdateUserProfile(BaseModel):
    model_config = {"from_attributes": True}

    name: str | None = Field(None, min_length=1, pattern=r"^\s*\S.*$")
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)
    avatar_url: str | None = None

