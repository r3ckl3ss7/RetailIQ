import enum

from db.database import Base
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    PAID = "paid"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    CREDIT = "credit"


class InvoiceSource(enum.Enum):
    ONLINE = "online"
    OCR = "ocr"
    MANUAL = "manual"
    API = "api"


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    invoices = relationship("Invoice", back_populates="customer")


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), nullable=False, unique=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True,
    )

    source = Column(
        Enum(InvoiceSource),
        default=InvoiceSource.ONLINE,
        nullable=False,
    )

    status = Column(
        Enum(InvoiceStatus),
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )

    subtotal = Column(Numeric(12, 2), default=0)
    total_discount = Column(Numeric(12, 2), default=0)
    total_tax = Column(Numeric(12, 2), default=0)
    round_off = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    paid_amount = Column(Numeric(12, 2), default=0)
    due_amount = Column(Numeric(12, 2), default=0)

    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)

    invoice_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    due_date = Column(DateTime(timezone=True), nullable=True)

    customer = relationship("Customer", back_populates="invoices")

    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    payments = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class InvoiceItem(Base, TimestampMixin):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False,
    )

    product_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    unit = Column(String(20), default="pcs")
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_price = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False,
    )

    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    transaction_reference = Column(String(255), nullable=True)
    payment_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")


 