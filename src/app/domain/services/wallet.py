import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories import (
    BalanceRepository,
    InstrumentRepository,
    UserRepository,
    WalletRepository,
)
from app.data.models import Balance, Wallet
from app.domain.entities import BalancesResponse, Deposit, UserCreate, UserResponse, Withdraw
from app.api.exceptions.exceptions import NotFoundException


class WalletService:
    def __init__(
        self,
        session: AsyncSession,
        balance_repo: BalanceRepository,
        instrument_repo: InstrumentRepository,
        wallet_repo: WalletRepository,
    ):
        self.session = session
        self.balance_repo = balance_repo
        self.instrument_repo = instrument_repo
        self.wallet_repo = wallet_repo

    async def get_instrument_balance(self, user_id: uuid.UUID, ticker: str) -> Balance | None:
        user_wallet_id = await self.wallet_repo.get_wallet_id_by_user_id(user_id=user_id)
        if not user_wallet_id:
            raise NotFoundException(entity_name='Wallet')

        instrument = await self.instrument_repo.get_instrument_by_ticker(ticker=ticker)
        if not instrument:
            raise NotFoundException(entity_name='Instrument')

        instrument_balance = await self.balance_repo.get_user_balance_of_instrument(
            wallet_id=user_wallet_id,
            instrument_id=instrument.id
        )
        return instrument_balance

    async def get_user_balances(self, user_id: uuid.UUID) -> BalancesResponse:
        user_wallet = await self.wallet_repo.get_wallet_by_user_id(user_id=user_id)
        balances = {balance.instrument.ticker: balance.amount for balance in user_wallet.balances}
        return BalancesResponse(balances=balances)

    async def deposit(self, deposit: Deposit) -> None:
        user_wallet_id = await self.wallet_repo.get_wallet_id_by_user_id(user_id=deposit.user_id)
        if not user_wallet_id:
            raise NotFoundException(entity_name='Wallet')

        instrument = await self.instrument_repo.get_instrument_by_ticker(ticker=deposit.ticker)
        if not instrument:
            raise NotFoundException(entity_name='Instrument')

        instrument_balance = await self.balance_repo.get_user_balance_of_instrument(
            wallet_id=user_wallet_id,
            instrument_id=instrument.id
        )

        if not instrument_balance:
            new_balance = Balance(
                wallet_id=user_wallet_id,
                instrument_id=instrument.id,
                amount=deposit.amount
            )
            await self.balance_repo.add(new_balance)
        else:
            await self.balance_repo.update_user_balance_of_instrument(
                balance_id=instrument_balance.id,
                amount=deposit.amount
            )
        
        await self.session.commit()

    async def withdraw(self, withdraw: Withdraw) -> None:
        instrument_balance = await self.get_instrument_balance(
            user_id=withdraw.user_id,
            ticker=withdraw.ticker
        )

        if not instrument_balance:
            raise NotFoundException(entity_name='Instrument balance')
        elif instrument_balance.amount >= withdraw.amount:
            await self.balance_repo.update_user_balance_of_instrument(
                balance_id=instrument_balance.id,
                amount=withdraw.amount * -1
            )
        else:
            raise HTTPException(status_code=400, detail='Insufficient funds')
        
        await self.session.commit()
