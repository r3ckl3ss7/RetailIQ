from db.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    JSON,
    Enum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum



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
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )



class Business(Base, TimestampMixin):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False, index=True)

    gst_number = Column(String(30), nullable=True, unique=True)

    phone = Column(String(20), nullable=True)

    email = Column(String(255), nullable=True)

    address = Column(Text, nullable=True)

    city = Column(String(100), nullable=True)

    state = Column(String(100), nullable=True)

    country = Column(String(100), default="India")

    postal_code = Column(String(20), nullable=True)

    logo_url = Column(Text, nullable=True)

    invoice_prefix = Column(String(20), nullable=True)

    currency = Column(String(10), default="INR")

    timezone = Column(String(100), default="Asia/Kolkata")

    invoices = relationship("Invoice", back_populates="business")


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=True)

    phone = Column(String(20), nullable=True, index=True)

    email = Column(String(255), nullable=True)

    gst_number = Column(String(30), nullable=True)

    address = Column(Text, nullable=True)

    city = Column(String(100), nullable=True)

    state = Column(String(100), nullable=True)

    country = Column(String(100), default="India")

    postal_code = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    invoices = relationship("Invoice", back_populates="customer")



class ProductCategory(Base, TimestampMixin):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False, unique=True)

    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    sku = Column(String(100), nullable=True, unique=True)

    barcode = Column(String(100), nullable=True, unique=True)

    name = Column(String(255), nullable=False, index=True)

    description = Column(Text, nullable=True)

    category_id = Column(
        Integer,
        ForeignKey("product_categories.id"),
        nullable=True
    )

    
    cost_price = Column(Numeric(12, 2), nullable=True)

    selling_price = Column(Numeric(12, 2), nullable=False)

    discount_percentage = Column(Float, default=0)

    tax_percentage = Column(Float, default=0)

    final_price = Column(Numeric(12, 2), nullable=True)

    
    stock_quantity = Column(Integer, default=0)

    minimum_stock_alert = Column(Integer, default=0)

    unit = Column(String(20), default="pcs")

    brand = Column(String(100), nullable=True)

    image_url = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    metadata_json = Column(JSON, nullable=True)

    category = relationship("ProductCategory", back_populates="products")

    invoice_items = relationship("InvoiceItem", back_populates="product")

    __table_args__ = (
        Index("idx_product_name", "name"),
    )

class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    invoice_number = Column(String(100), nullable=False, unique=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True
    )

    source = Column(
        Enum(InvoiceSource),
        default=InvoiceSource.ONLINE
    )

    status = Column(
        Enum(InvoiceStatus),
        default=InvoiceStatus.DRAFT
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

    festive_offer_name = Column(String(255), nullable=True)

    invoice_date = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    due_date = Column(DateTime(timezone=True), nullable=True)

    raw_ocr_text = Column(Text, nullable=True)

    ocr_confidence_score = Column(Float, nullable=True)

    ocr_metadata = Column(JSON, nullable=True)

    external_reference = Column(String(255), nullable=True)

    business = relationship("Business", back_populates="invoices")

    customer = relationship("Customer", back_populates="invoices")

    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    payments = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_invoice_number", "invoice_number"),
        Index("idx_invoice_date", "invoice_date"),
    )



class InvoiceItem(Base, TimestampMixin):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True
    )

    product_name = Column(String(255), nullable=False)

    product_sku = Column(String(100), nullable=True)

    quantity = Column(Float, nullable=False, default=1)

    unit = Column(String(20), default="pcs")

    unit_price = Column(Numeric(12, 2), nullable=False)

    discount_percentage = Column(Float, default=0)

    discount_amount = Column(Numeric(12, 2), default=0)

    tax_percentage = Column(Float, default=0)

    tax_amount = Column(Numeric(12, 2), default=0)

    total_price = Column(Numeric(12, 2), nullable=False)

    metadata_json = Column(JSON, nullable=True)

    invoice = relationship("Invoice", back_populates="items")

    product = relationship("Product", back_populates="invoice_items")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False
    )

    amount = Column(Numeric(12, 2), nullable=False)

    payment_method = Column(
        Enum(PaymentMethod),
        nullable=False
    )

    transaction_reference = Column(String(255), nullable=True)

    payment_date = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    notes = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")


class OCRDocument(Base, TimestampMixin):
    __tablename__ = "ocr_documents"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=True
    )

    original_file_name = Column(String(255), nullable=True)

    file_url = Column(Text, nullable=False)

    mime_type = Column(String(100), nullable=True)

    extracted_text = Column(Text, nullable=True)

    parsed_json = Column(JSON, nullable=True)

    confidence_score = Column(Float, nullable=True)

    processing_status = Column(String(50), default="pending")

    error_message = Column(Text, nullable=True)



class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    table_name = Column(String(100), nullable=False)

    record_id = Column(Integer, nullable=False)

    action = Column(String(50), nullable=False)

    old_data = Column(JSON, nullable=True)

    new_data = Column(JSON, nullable=True)

    performed_by = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


