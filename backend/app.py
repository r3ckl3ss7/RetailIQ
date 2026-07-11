from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import text

from db.database import async_engine
from models.user import create_table
from routes.auth import router as authRouter
from routes.invoice import router as invoiceRouter
from routes.user import router as userRouter
from routes.products import router as productsRouter
from routes.analytics import router as analyticsRouter
from routes.ai import router as aiRouter
from routes.upload import router as uploadRouter

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
uploads_dir = BASE_DIR / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get('/')
async def home():
    return {"Message": "Started"}


@app.get('/db-health')
async def db_health():
    async with async_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return {"database": "connected"}


app.include_router(authRouter)
app.include_router(invoiceRouter)
app.include_router(userRouter)
app.include_router(productsRouter)
app.include_router(analyticsRouter)
app.include_router(aiRouter)
app.include_router(uploadRouter)


