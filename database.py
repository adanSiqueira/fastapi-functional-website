from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

#Async imports
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import settings


engine = create_async_engine(
    settings.database_url
)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_ = AsyncSession,
    expire_on_commit = False,
)


class Base(DeclarativeBase):
    pass

# def get_db():
#     with SessionLocal() as db:
#         yield db

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
