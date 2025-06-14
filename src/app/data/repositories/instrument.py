from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import SQLAlchemyRepository
from app.data.models import Instrument


class InstrumentRepository(SQLAlchemyRepository[Instrument]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Instrument)

    async def get_instrument_by_ticker(self, ticker: str) -> Instrument | None:
        query = select(Instrument).where(Instrument.ticker == ticker)
        result = await self.session.scalar(query)
        return result