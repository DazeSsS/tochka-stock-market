from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Generic, TypeVar, Optional

from database import Base 


ModelType = TypeVar("ModelType", bound=Base)


class SQLAlchemyRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        query = select(self.model)
        result = await self.session.scalars(query)
        return result.all()

    async def get_by_id(self, id: Any) -> ModelType | None:
        result = await self.session.get(self.model, id)
        return result

    async def add(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelType) -> ModelType:
        await self.session.delete(obj)
        await self.session.flush()
        return obj
