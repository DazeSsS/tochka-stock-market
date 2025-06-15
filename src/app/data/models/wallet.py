import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship, Mapped

from database import Base
from app.data.types import CreatedAt, ID


class Wallet(Base):
    __tablename__ = 'wallets'

    id: Mapped[ID]
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)

    user: Mapped['User'] = relationship(back_populates='wallet')
    balances: Mapped[list['Balance']] = relationship(back_populates='wallet', cascade='all, delete-orphan')
    transactions: Mapped[list['Transaction']] = relationship(back_populates='wallet', cascade='all, delete-orphan')
