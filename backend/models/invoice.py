import enum

from db.database import Base
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class InvoiceStatus(enum.Enum):
    PENDING = 'PENDING'
    DRAFT = 'DRAFT'
    PAID = 'PAID'
    REFUNDED = 'REFUNDED'
    CANCELLED = 'CANCELLED'


class PaymentMethod(enum.Enum):
    CASH = 'CASH'
    UPI = 'UPI'
    CARD = 'CARD'
    CHEQUE = 'CHEQUE'
    OTHER = 'OTHER'


class InvoiceSource(enum.Enum):
    ONLINE = 'ONLINE'


class CustomerAddress(Base):
    __tablename__ = 'customer_address'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customer.id', ondelete='CASCADE'), nullable=False)
    line1 = Column(String(255), nullable=False)
    line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    customer = relationship('Customer', back_populates='address')


class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone_number_country_code = Column(String(5), default='+91')
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    address = relationship('CustomerAddress', back_populates='customer', uselist=False, cascade='all, delete-orphan')
    business = relationship('Business', back_populates='customers')


class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(String(20), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    business = relationship('Business', back_populates='payments')


class Invoice(Base):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customer.id', ondelete='SET NULL'), nullable=True, index=True)
    payment_id = Column(Integer, ForeignKey('payment.id', ondelete='SET NULL'), nullable=True)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING)
    source = Column(Enum(InvoiceSource), nullable=False, default=InvoiceSource.ONLINE)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax = Column(Numeric(12, 2), nullable=False, default=0)
    discount = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    customer = relationship('Customer')
    payment = relationship('Payment')
    items = relationship('InvoiceItem', back_populates='invoice', cascade='all, delete-orphan')
    business = relationship('Business', back_populates='invoices')


class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoice.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    invoice = relationship('Invoice', back_populates='items')
    product = relationship('Product')