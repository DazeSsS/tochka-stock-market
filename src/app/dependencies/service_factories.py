from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from redis.asyncio import Redis
from config import settings
from database import get_async_session

from app.data.repositories import (
    BalanceRepository,
    InstrumentRepository,
    OrderRepository,
    OrderBookRepository,
    TransactionRepository,
    UserRepository,
    WalletRepository,
)
from app.domain.services import (
    InstrumentService,
    OrderService,
    TransactionService,
    UserService,
    WalletService,
)


def get_instrument_service(session: Annotated[AsyncSession, Depends(get_async_session)]) -> InstrumentService:
    instrument_repo = InstrumentRepository(session)
    return InstrumentService(session, instrument_repo)

def get_order_service(session: Annotated[AsyncSession, Depends(get_async_session)]) -> OrderService:
    redis = Redis(
        host='redis',
        port=6379,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )
    orderbook = OrderBookRepository(redis=redis)

    balance_repo = BalanceRepository(session)
    instrument_repo = InstrumentRepository(session)
    order_repo = OrderRepository(session)
    transaction_repo = TransactionRepository(session)
    wallet_repo = WalletRepository(session)
    return OrderService(session, balance_repo, instrument_repo, order_repo, orderbook, transaction_repo, wallet_repo)

def get_transaction_service(session: Annotated[AsyncSession, Depends(get_async_session)]) -> TransactionService:
    instrument_repo = InstrumentRepository(session)
    transaction_repo = TransactionRepository(session)
    return TransactionService(session, instrument_repo, transaction_repo)

def get_user_service(session: Annotated[AsyncSession, Depends(get_async_session)]) -> UserService:
    balance_repo = BalanceRepository(session)
    instrument_repo = InstrumentRepository(session)
    user_repo = UserRepository(session)
    wallet_repo = WalletRepository(session)
    return UserService(session, balance_repo, instrument_repo, user_repo, wallet_repo)

def get_wallet_service(session: Annotated[AsyncSession, Depends(get_async_session)]) -> WalletService:
    balance_repo = BalanceRepository(session)
    instrument_repo = InstrumentRepository(session)
    wallet_repo = WalletRepository(session)
    return WalletService(session, balance_repo, instrument_repo, wallet_repo)
