from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import SQLAlchemyRepository
from app.data.models import Transaction


class TransactionRepository(SQLAlchemyRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Transaction)

    async def get_all_transactions_by_instrument(self, instrument_id: int, limit: int) -> list[Transaction]:
        query = (
            select(Transaction)
            .where(Transaction.instrument_id == instrument_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.scalars(query)
        return result
