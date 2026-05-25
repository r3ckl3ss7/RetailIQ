from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, Column, ForeignKey, Text, DateTime, func
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


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    business_name = Column(String(255), nullable=False)

    category = Column(String(100), nullable=False)

    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="businesses")

    contact_details = relationship(
        "ContactDetails",
        back_populates="business",
        uselist=False,
        cascade="all, delete"
    )


class ContactDetails(Base):
    __tablename__ = "contact_details"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    phone_number = Column(String(20), nullable=False)

    alt_phone_no = Column(String(20))

    city = Column(String(100), nullable=False)

    district = Column(String(100))

    state = Column(String(100), nullable=False)

    country = Column(String(100), nullable=False)

    postal_code = Column(String(20), nullable=False)

    address_line = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="contact_details")


def create_table():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Table created!")
