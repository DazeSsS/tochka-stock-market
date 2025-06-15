from fastapi import HTTPException

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import SQLAlchemyRepository
from app.data.models import Balance


class BalanceRepository(SQLAlchemyRepository[Balance]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Balance)

    async def get_user_balance_of_instrument(self, wallet_id: int, instrument_id: int) -> Balance | None:
        query = (
            select(Balance)
            .where(
                Balance.wallet_id == wallet_id,
                Balance.instrument_id == instrument_id
            )
            .with_for_update()
        )
        result = await self.session.scalar(query)
        return result

    async def update_user_balance_of_instrument(self, balance_id: int, amount: int) -> None:
        stmt = (
            update(Balance)
            .where(Balance.id == balance_id)
            .values(amount=Balance.amount + amount)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def reserve(self, wallet_id: int, instrument_id: int, amount: int):
        """Резервируем средства на балансе"""
        balance = await self.get_user_balance_of_instrument(wallet_id, instrument_id)
        if not balance:
            raise HTTPException(status_code=400, detail="Balance not found")
        
        if balance.amount < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        balance.reserved += amount
        await self.session.flush()

    async def release(self, wallet_id: int, instrument_id: int, amount: int):
        """Освобождаем зарезервированные средства"""
        balance = await self.get_user_balance_of_instrument(wallet_id, instrument_id)
        if not balance:
            raise HTTPException(status_code=400, detail="Balance not found")
        
        if balance.reserved < amount:
            raise HTTPException(status_code=400, detail="Insufficient reserved funds")
        
        balance.reserved -= amount
        await self.session.flush()

    async def transfer(
        self, 
        from_wallet_id: int, 
        to_wallet_id: int, 
        instrument_id: int, 
        amount: int
    ):
        from_balance = await self.get_user_balance_of_instrument(from_wallet_id, instrument_id)
        to_balance = await self.get_user_balance_of_instrument(to_wallet_id, instrument_id)
        
        if not from_balance:
            raise HTTPException(status_code=400, detail="Sender balance not found")
            
        if not to_balance:
            to_balance = Balance(
                wallet_id=to_wallet_id,
                instrument_id=instrument_id,
                amount=0,
                reserved=0
            )
            self.session.add(to_balance)
            await self.session.flush()
        
        # Проверяем доступный баланс (общий - зарезервированный)
        available = from_balance.amount - from_balance.reserved
        if available < amount:
            raise HTTPException(status_code=400, detail="Insufficient available funds")
        
        from_balance.amount -= amount
        to_balance.amount += amount
        await self.session.flush()
