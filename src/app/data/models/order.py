import uuid

from sqlalchemy import text, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, relationship, Mapped

from database import Base
from app.data.types import CreatedAt, ID
from app.domain.enums import OrderDirection, OrderStatus, OrderType


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(String(8))
    status: Mapped[OrderStatus] = mapped_column(String(32), server_default=OrderStatus.NEW)
    direction: Mapped[OrderDirection] = mapped_column(String(8))
    qty: Mapped[int]
    price: Mapped[int] = mapped_column(Integer, server_default='0')
    filled: Mapped[int] = mapped_column(Integer, server_default='0')
    timestamp: Mapped[CreatedAt]

    user: Mapped['User'] = relationship(back_populates='orders')
    instrument: Mapped['Instrument'] = relationship(back_populates='orders')
