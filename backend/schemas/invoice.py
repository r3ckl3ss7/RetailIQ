from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, condecimal, conint

Money = condecimal(max_digits=12, decimal_places=2, ge=0)
PositiveInt = conint(gt=0)


class InvoiceStatus(str, Enum):
    PENDING = 'PENDING'
    DRAFT = 'DRAFT'
    PAID = 'PAID'
    REFUNDED = 'REFUNDED'
    CANCELLED = 'CANCELLED'


class InvoiceSource(str, Enum):
    ONLINE = 'ONLINE'
    OCR = 'OCR'


class InvoiceItemBase(BaseModel):
    product_id: int
    quantity: PositiveInt


class InvoiceBase(BaseModel):
    business_id: int
    customer_id: Optional[int] = None
    payment_id: Optional[int] = None
    status: InvoiceStatus = InvoiceStatus.PENDING
    source: InvoiceSource = InvoiceSource.ONLINE
    subtotal: Money = 0
    tax: Money = 0
    discount: Money = 0
    total: Money = 0
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    items: Annotated[list[InvoiceItemBase], Field(min_length=1)]


class InvoiceUpdate(BaseModel):
    customer_id: Optional[int] = None
    payment_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    source: Optional[InvoiceSource] = None
    subtotal: Optional[Money] = None
    tax: Optional[Money] = None
    discount: Optional[Money] = None
    total: Optional[Money] = None
    notes: Optional[str] = None
    items: Optional[list[InvoiceItemBase]] = None


class InvoiceResponse(InvoiceBase):
    id: int
    items: list[InvoiceItemBase]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceMetadata(BaseModel):
    customer_name: str
    status: InvoiceStatus
    tax: Money = 0
    discount: Money = 0
    total: Money = 0


class CustomerInput(BaseModel):
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None


class InvoiceItemInput(BaseModel):
    product_id: Optional[int] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    quantity: PositiveInt


class InvoiceCreatePayload(BaseModel):
    business_id: int
    customer_id: Optional[int] = None
    customer: Optional[CustomerInput] = None
    payment_id: Optional[int] = None
    status: InvoiceStatus = InvoiceStatus.PENDING
    source: InvoiceSource = InvoiceSource.ONLINE
    subtotal: Optional[Money] = None
    tax: Optional[Money] = None
    discount: Optional[Money] = None
    total: Optional[Money] = None
    notes: Optional[str] = None
    items: Annotated[list[InvoiceItemInput], Field(min_length=1)]

