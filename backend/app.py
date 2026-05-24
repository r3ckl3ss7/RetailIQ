from fastapi import FastAPI
from sqlalchemy import text

from db.database import engine

app = FastAPI()


@app.get('/')
def home():
    return {"Message": "Started"}


@app.get('/db-health')
def db_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"database": "connected"}
