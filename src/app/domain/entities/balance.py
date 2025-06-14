from pydantic import field_validator, Field
from app.domain.entities import BaseSchema


class BalancesResponse(BaseSchema):
    balances: dict[str, int]

    @field_validator('balances')
    def check_positive(cls, value: dict[str, int]):
        for item in value.values():
            if item < 0:
                raise ValueError('Balance cannot be negative')
        return value
