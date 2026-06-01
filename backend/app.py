from fastapi import FastAPI
from sqlalchemy import text

from db.database import async_engine
from models.user import create_table
from routes.auth import router as authRouter
from routes.invoice import router as invoiceRouter
from routes.user import router as userRouter
app = FastAPI()


@app.get('/')
async def home():
    return {"Message": "Started"}


@app.get('/create-tables')
async def create_tables():
    await create_table()


@app.get('/db-health')
async def db_health():
    async with async_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return {"database": "connected"}


app.include_router(authRouter)
app.include_router(invoiceRouter)
app.include_router(userRouter)
