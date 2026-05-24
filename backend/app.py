from fastapi import FastAPI
from sqlalchemy import text

from db.database import engine
from db.database import Base
from schemas.user import create_table, test_push
app = FastAPI()


@app.get('/')
def home():
    return {"Message": "Started"}

@app.get('/create-tables')
def create_tables():
    create_table()
    test_push()
    
@app.get('/db-health')
def db_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"database": "connected"}
