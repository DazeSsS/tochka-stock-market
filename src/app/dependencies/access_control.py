from fastapi import status, Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.domain.services import UserService
from app.domain.entities import UserResponse
from app.domain.enums import UserRole
from app.dependencies.service_factories import get_user_service
from app.api.exceptions.exceptions import (
    AccessDeniedException,
    InvalidAPIKeyException,
    InvalidAuthorizationFormatException,
    NotFoundException,
)

api_key_header = APIKeyHeader(name='Authorization')

async def get_current_user(
    authorization: str = Depends(api_key_header),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    if not authorization or not authorization.startswith('TOKEN '):
        raise InvalidAuthorizationFormatException()

    # TODO add cache

    api_key = authorization.split(' ')[1]

    try:
        async with user_service.session.begin():
            user = await user_service.get_user_by_api_key(api_key=api_key)
    except NotFoundException:
        raise InvalidAPIKeyException()

    return UserResponse.model_validate(user)


async def get_admin_user(
    user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    if user.role != UserRole.ADMIN:
        raise AccessDeniedException()
    return user
