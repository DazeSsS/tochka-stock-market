import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import SQLAlchemyRepository
from app.data.models import Order
from app.domain.enums import OrderStatus


class OrderRepository(SQLAlchemyRepository[Order]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    async def update_filled(self, order_id: uuid.UUID, fill_qty: int) -> OrderStatus:
        order = await self.session.get(Order, order_id)
        
        order.filled += fill_qty
        
        if order.filled >= order.qty:
            order.status = OrderStatus.EXECUTED
        elif order.filled > 0:
            order.status = OrderStatus.PARTIALLY_EXECUTED
        
        self.session.add(order)
        await self.session.flush()
        return order.status

    async def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> None:
        order = await self.session.get(Order, order_id)
        
        order.status = status
        
        self.session.add(order)
        await self.session.flush()

    async def get_user_orders(self, user_id: uuid.UUID) -> list[Order]:
        query = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.timestamp.desc())
        )
        result = await self.session.scalars(query)
        return result
