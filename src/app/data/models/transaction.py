from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship, Mapped

from database import Base
from app.data.types import CreatedAt, ID


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[ID]
    instrument_id: Mapped[str] = mapped_column(ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False)
    wallet_id: Mapped[int] = mapped_column(ForeignKey('wallets.id', ondelete='CASCADE'), nullable=False)
    amount: Mapped[int]
    price: Mapped[int]
    timestamp: Mapped[CreatedAt]

    instrument: Mapped['Instrument'] = relationship(back_populates='transactions')
    wallet: Mapped['Wallet'] = relationship(back_populates='transactions')
