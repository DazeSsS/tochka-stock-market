from datetime import datetime
from pydantic import Field

from app.domain.entities import BaseSchema


class TransactionResponse(BaseSchema):
    ticker: str
    amount: int
    price: int
    timestamp: datetime
