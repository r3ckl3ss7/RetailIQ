import asyncio
import os
import sys
import subprocess
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def wait_for_db_and_seed():
    url = os.getenv("ASYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL / ASYNC_DATABASE_URL not set. Skipping DB check.")
        return

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("Connecting to database:", url.split("@")[-1])
    engine = create_async_engine(url, pool_pre_ping=True)

    max_retries = 30
    connected = False
    for i in range(max_retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                connected = True
                print("Database is ready!")
                break
        except Exception as e:
            print(f"Waiting for database... ({i+1}/{max_retries}): {e}")
            await asyncio.sleep(1)

    if not connected:
        print("Could not connect to the database. Exiting.")
        sys.exit(1)

    # Check and seed
    try:
        async with engine.connect() as conn:
            # Check if 'users' table exists
            res = await conn.execute(text(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'users');"
            ))
            exists = res.scalar()
            if not exists:
                print("Database tables not found. Running seed script...")
                # Run seed.py
                result = subprocess.run([sys.executable, "seed.py"], check=True)
                if result.returncode == 0:
                    print("Database seeding completed successfully.")
                else:
                    print("Seeding failed.")
                    sys.exit(1)
            else:
                print("Database already initialized. Skipping seeding.")
    except Exception as e:
        print("Error checking or seeding database:", e)
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == '__main__':
    asyncio.run(wait_for_db_and_seed())
