from typing import Annotated

from fastapi import APIRouter, Depends

from app.domain.services import WalletService
from app.domain.entities import UserResponse
from app.dependencies import get_current_user, get_wallet_service


router = APIRouter(
    prefix='/balance',
    tags=['Balance']
)


@router.get('')
async def get_balances(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> dict[str, int]:
    user_balances = await wallet_service.get_user_balances(user_id=current_user.id)
    return user_balances.balances
