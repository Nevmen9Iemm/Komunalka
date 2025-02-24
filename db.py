# db.py
import datetime
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models import Base

DATABASE_URL = "sqlite+aiosqlite:///komunalka.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database initialized.")

async def async_clear_old_bills():
    from models import Bill  # імпортуємо Bill із models
    from sqlalchemy import select
    try:
        async with async_session() as session:
            two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2*365)
            stmt = select(Bill).where(Bill.created_at < two_years_ago)
            result = await session.execute(stmt)
            old_bills = result.scalars().all()
            for bill in old_bills:
                await session.delete(bill)
            await session.commit()
            logging.info("Старі рахунки очищено.")
    except Exception as e:
        logging.error(f"Помилка при очищенні старих рахунків: {e}")
