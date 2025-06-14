import uuid
from datetime import datetime
from pydantic import Field

from app.domain.entities import BaseSchema
from app.domain.enums import OrderDirection, OrderStatus


class MarketOrderCreate(BaseSchema):
    direction: OrderDirection
    ticker: str
    qty: int = Field(ge=1)


class LimitOrderCreate(MarketOrderCreate):
    price: int = Field(gt=0)


class OrderResponse(BaseSchema):
    id: uuid.UUID
    status: OrderStatus
    user_id: uuid.UUID
    timestamp: datetime


class MarketOrderResponse(OrderResponse):
    body: MarketOrderCreate


class LimitOrderResponse(OrderResponse):
    body: LimitOrderCreate
    filled: int


class SuccessOrderResponse(BaseSchema):
    success: bool = True
    order_id: uuid.UUID


class LevelsResponse(BaseSchema):
    price: int
    qty: int


class OrderBookResponse(BaseSchema):
    bid_levels: list[LevelsResponse]
    ask_levels: list[LevelsResponse]
