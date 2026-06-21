from db.database import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func


class Auth(Base):
    __tablename__ = 'auth'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    token = Column(
        String,
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())