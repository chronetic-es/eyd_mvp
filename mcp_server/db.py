import asyncpg
from config import DATABASE_URL


async def obtener_conexion_db():
    return await asyncpg.connect(DATABASE_URL)
