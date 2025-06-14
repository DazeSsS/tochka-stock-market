from sqlalchemy import String
from sqlalchemy.orm import mapped_column, relationship, Mapped

from database import Base
from app.data.types import CreatedAt, ID


class Instrument(Base):
    __tablename__ = 'instruments'

    id: Mapped[ID]
    ticker: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[CreatedAt]

    orders: Mapped[list['Order']] = relationship(back_populates='instrument', cascade='all, delete-orphan')
    transactions: Mapped[list['Transaction']] = relationship(back_populates='instrument', cascade='all, delete-orphan')
