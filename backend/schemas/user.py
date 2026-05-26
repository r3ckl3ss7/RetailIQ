from pydantic import BaseModel, EmailStr
from datetime import datetime


class User(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    email: EmailStr
    created_at: datetime


class ContactDetails(BaseModel):
    model_config = {"from_attributes": True}

    id: int | None = None
    phone_number: str
    alt_phone_no: str | None = None
    city: str
    district: str | None = None
    state: str
    country: str
    postal_code: str
    address_line: str | None = None
    created_at: datetime | None = None


class Business(BaseModel):
    model_config = {"from_attributes": True}

    id: int | None = None
    business_name: str
    category: str
    description: str | None = None
    created_at: datetime | None = None
    contact_details: ContactDetails | None = None


class UpdatedContactDetails(BaseModel):
    model_config = {"from_attributes": True}
    id: int | None = None
    phone_number: str
    alt_phone_no: str | None = None
    city: str
    district: str | None = None
    state: str
    country: str
    postal_code: str
    address_line: str | None = None
    created_at: datetime | None = None


class UpdatedBusiness(BaseModel):
    model_config = {"from_attributes": True}

    business_name: str
    category: str
    description: str | None = None
    contact_details: ContactDetails | None = None


class UpdateUserProfile(BaseModel):
    model_config = {"from_attributes": True}

    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
