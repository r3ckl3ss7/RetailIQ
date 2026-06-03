from sqlalchemy.orm import relationship
from sqlalchemy import (
    Integer,
    String,
    Column,
    ForeignKey,
    Text,
    DateTime,
    func,
)
from db.database import Base, async_engine


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, nullable=False, index=True)

    password = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    businesses = relationship(
        "Business",
        back_populates="owner",
        cascade="all, delete"
    )


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

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

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="businesses")
    products = relationship(
        "Product",
        back_populates="business",
        cascade="all, delete",
    )


async def create_table():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Table created!")
