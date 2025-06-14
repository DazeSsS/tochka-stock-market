import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories import InstrumentRepository, TransactionRepository
from app.data.models import Instrument
from app.api.exceptions.exceptions import NotFoundException


class TransactionService:
    def __init__(
        self,
        session: AsyncSession,
        instrument_repo: InstrumentRepository,
        transaction_repo: TransactionRepository,
    ):
        self.session = session
        self.instrument_repo = instrument_repo
        self.transaction_repo = transaction_repo

    async def get_transactions(self, ticker: str, limit: int):
        instrument = await self.instrument_repo.get_instrument_by_ticker(ticker=ticker)

        if not instrument:
            raise NotFoundException(entity_name='Instrument')

        transactions = await self.transaction_repo.get_all_transactions_by_instrument(instrument_id=instrument.id, limit=limit)
        return transactions
