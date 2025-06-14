import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import SQLAlchemyRepository
from app.data.models import Balance, Wallet


class WalletRepository(SQLAlchemyRepository[Wallet]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Wallet)

    async def get_wallet_id_by_user_id(self, user_id: uuid.UUID) -> int | None:
        query = select(Wallet.id).where(Wallet.user_id == user_id)
        result = await self.session.scalar(query)
        return result

    async def get_wallet_by_user_id(self, user_id: uuid.UUID) -> Wallet | None:
        query = (
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .options(selectinload(Wallet.balances).joinedload(Balance.instrument))
        )
        result = await self.session.scalar(query)
        return result
