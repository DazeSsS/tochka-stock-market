import uuid
from pydantic import Field
from app.domain.entities import BaseSchema


class Deposit(BaseSchema):
    user_id: uuid.UUID
    ticker: str
    amount: int = Field(gt=0)


class Withdraw(Deposit):
    pass
