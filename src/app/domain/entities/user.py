import uuid
from datetime import datetime
from pydantic import Field

from app.domain.entities import BaseSchema
from app.domain.enums import UserRole


class UserCreate(BaseSchema):
    name: str = Field(min_length=3)


class UserResponse(UserCreate):
    id: uuid.UUID
    role: UserRole
    api_key: str
