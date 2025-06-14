import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Security

from app.domain.services import InstrumentService, UserService, WalletService
from app.domain.entities import Deposit, InstrumentCreate, UserCreate, UserResponse, Withdraw
from app.api.exceptions.schemas import SuccessResponse
from app.dependencies import get_admin_user, get_instrument_service, get_user_service, get_wallet_service


router = APIRouter(
    prefix='/admin',
    tags=['Admin']
)


@router.delete('/user/{user_id}')
async def delete_user(
    user_id: uuid.UUID,
    admin_user: Annotated[UserResponse, Security(get_admin_user)],
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponse:
    deleted_user = await user_service.delete_user_by_id(user_id=user_id)
    return deleted_user


@router.post('/instrument')
async def add_instrument(
    instrument: InstrumentCreate,
    admin_user: Annotated[UserResponse, Security(get_admin_user)],
    instrument_service: Annotated[InstrumentService, Depends(get_instrument_service)]
) -> SuccessResponse:
    new_instrument = await instrument_service.create_instrument(instrument=instrument)
    if new_instrument:
        return SuccessResponse()


@router.delete('/instrument/{ticker}')
async def delete_instrument(
    ticker: str,
    admin_user: Annotated[UserResponse, Security(get_admin_user)],
    instrument_service: Annotated[InstrumentService, Depends(get_instrument_service)]
) -> SuccessResponse:
    await instrument_service.delete_instument_by_ticker(ticker=ticker)
    return SuccessResponse()


@router.post('/balance/deposit', tags=['Balance'])
async def deposit(
    deposit: Deposit,
    admin_user: Annotated[UserResponse, Security(get_admin_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)]
) -> SuccessResponse:
    await wallet_service.deposit(deposit=deposit)
    return SuccessResponse()


@router.post('/balance/withdraw', tags=['Balance'])
async def withdraw(
    withdraw: Withdraw,
    admin_user: Annotated[UserResponse, Security(get_admin_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)]
) -> SuccessResponse:
    await wallet_service.withdraw(withdraw=withdraw)
    return SuccessResponse()
