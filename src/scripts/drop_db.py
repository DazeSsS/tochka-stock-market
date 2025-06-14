import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from database import Base
from config import settings


DATABASE_URL = settings.get_db_url()

engine = create_async_engine(DATABASE_URL)

metadata = Base.metadata


async def reflect_metadata():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.reflect)

async def drop_all_tables():
    print('Dropping all tables...')
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)

async def drop_db():
    await reflect_metadata()
    await drop_all_tables()
    print('Done')
    

if __name__ == '__main__':
    confirm = input('WARNING: This will DROP ALL TABLES. Are you sure? [y/n]: ')
    if confirm.lower() == 'y':
        asyncio.run(drop_db())
    else:
        print('Operation cancelled.')
