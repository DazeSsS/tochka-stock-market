import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import SQLAlchemyRepository
from app.data.models import User


class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_user_by_api_key(self, api_key: str) -> User | None:
        query = (
            select(User)
            .where(User.api_key == api_key)
        )
        result = await self.session.scalar(query)
        return result
