from sqlalchemy import Integer, String, Column
from db.database import Base, engine, SessionLocal

session = SessionLocal()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100), unique=True)


def create_table():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Table created!")


