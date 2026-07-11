import redis
import os
from dotenv import load_dotenv
import asyncio
load_dotenv()

redisClient=redis.Redis(host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    decode_responses=bool(os.getenv('REDIS_DECODE_RESPONSES')),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv('REDIS_PASSWORD'),
    )  

