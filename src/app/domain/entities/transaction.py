from datetime import datetime
from pydantic import Field

from app.domain.entities import BaseSchema


class TransactionResponse(BaseSchema):
    name: str
    ticker: str = Field(pattern=r'^[A-Z]{2,10}$')
