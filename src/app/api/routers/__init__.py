from fastapi import APIRouter
from .admin import router as admin_router
from .balance import router as balance_router
from .order import router as order_router
from .public import router as public_router


api_router = APIRouter(
    prefix='/api/v1'
)

api_router.include_router(public_router)
api_router.include_router(balance_router)
api_router.include_router(order_router)
api_router.include_router(admin_router)
