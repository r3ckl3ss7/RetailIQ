from fastapi import FastAPI
from sqlalchemy import text

from db.database import engine
from models.user import create_table
from routes.auth import router as authRouter
from routes.invoice import router as invoiceRouter
from routes.user import router as userRouter
app = FastAPI()


@app.get('/')
def home():
    return {"Message": "Started"}


@app.get('/create-tables')
def create_tables():
    create_table()


@app.get('/db-health')
def db_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"database": "connected"}


app.include_router(authRouter)
app.include_router(invoiceRouter)
app.include_router(userRouter)
