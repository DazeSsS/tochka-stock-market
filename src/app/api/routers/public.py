import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.domain.services import (
    InstrumentService,
    OrderService,
    TransactionService,
    UserService,
)
from app.domain.entities import (
    InstrumentResponse,
    OrderBookResponse,
    TransactionResponse,
    UserCreate,
    UserResponse,
)
from app.dependencies import (
    get_instrument_service,
    get_order_service,
    get_transaction_service,
    get_user_service,
)


router = APIRouter(
    prefix='/public',
    tags=['Public']
)


@router.post('/register')
async def register(
    new_user: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponse:
    created_user = await user_service.create_user(user=new_user)
    return created_user


@router.get('/instrument')
async def list_instruments(
    instrument_service: Annotated[InstrumentService, Depends(get_instrument_service)]
) -> list[InstrumentResponse]:
    instruments = await instrument_service.get_all_instruments()
    return instruments


@router.get('/orderbook/{ticker}')
async def get_orderbook(
    ticker: str,
    order_service: Annotated[OrderService, Depends(get_order_service)],
    limit: int = 10,
) -> OrderBookResponse:
    orderbook = await order_service.get_orderbook(ticker=ticker, limit=limit)
    return orderbook


@router.get('/transactions/{ticker}')
async def get_transaction_history(
    ticker: str,
    transaction_service: Annotated[TransactionService, Depends(get_transaction_service)],
    limit: int = 10,
) -> list[TransactionResponse]:
    transactions = await transaction_service.get_transactions(ticker=ticker, limit=limit)
    return transactions
