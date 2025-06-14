import uuid

from sqlalchemy import text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, relationship, Mapped

from database import Base
from app.data.types import CreatedAt
from app.domain.enums import UserRole


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String(128))
    role: Mapped[UserRole] = mapped_column(String(5))
    api_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[CreatedAt]

    wallet: Mapped['Wallet'] = relationship(back_populates='user', uselist=False, cascade='all, delete-orphan')
    orders: Mapped[list['Order']] = relationship(back_populates='user', cascade='all, delete-orphan')
