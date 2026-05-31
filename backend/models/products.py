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



class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False, index=True)
    original_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    sku = Column(String(50), nullable=True, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    business = relationship('Business', back_populates='products')
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
