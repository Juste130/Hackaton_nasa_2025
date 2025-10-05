"""
Clear asyncpg prepared statement cache
"""
import asyncio
from sqlalchemy import text
from client import DatabaseClient

async def clear_cache():
    client = DatabaseClient()
    try:
        async with client.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            #await conn.execute("SELECT 1")
            print(" Cache cleared, try embeddings_generator.py again")
    finally:
        await client.close()

asyncio.run(clear_cache())