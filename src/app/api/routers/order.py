import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.domain.services import OrderService, WalletService
from app.domain.entities import (
    LimitOrderCreate,
    LimitOrderResponse,
    MarketOrderCreate,
    MarketOrderResponse,
    SuccessOrderResponse,
    UserResponse,
)
from app.dependencies import get_current_user, get_order_service
from app.api.exceptions.schemas import SuccessResponse


router = APIRouter(
    prefix='/order',
    tags=['Order']
)


@router.post('')
async def create_order(
    order: LimitOrderCreate | MarketOrderCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessOrderResponse:
    new_order = await order_service.create_order(user_id=current_user.id, order=order)
    return new_order


@router.get('')
async def list_orders(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> list[LimitOrderResponse | MarketOrderResponse]:
    user_orders = await order_service.list_orders(user_id=current_user.id)
    return user_orders


@router.get('/{order_id}')
async def get_order(
    order_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> LimitOrderResponse | MarketOrderResponse:
    user_order = await order_service.get_order_by_id(user_id=current_user.id, order_id=order_id)
    return user_order


@router.delete('/{order_id}')
async def cancel_order(
    order_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse:
    await order_service.cancel_order(order_id=order_id, user_id=current_user.id)
    return SuccessResponse()
