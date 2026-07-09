import redis
import asyncio

redisClient=redis.Redis(host='localhost',port=6379,decode_responses=True)

