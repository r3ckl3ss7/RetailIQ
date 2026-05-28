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
from db.database import Base, engine, SessionLocal

session = SessionLocal()


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


# Align Business model with backend/models/invoice.py while keeping ownership
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


def create_table():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Table created!")
