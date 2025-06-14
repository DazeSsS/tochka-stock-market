from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship, Mapped

from database import Base
from app.data.types import CreatedAt, ID


class Balance(Base):
    __tablename__ = 'balances'

    id: Mapped[ID]
    wallet_id: Mapped[int] = mapped_column(ForeignKey('wallets.id', ondelete='CASCADE'), nullable=False)
    instrument_id: Mapped[str] = mapped_column(ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, server_default='0')
    reserved: Mapped[int] = mapped_column(Integer, server_default='0')

    wallet: Mapped['Wallet'] = relationship(back_populates='balances')
    instrument: Mapped['Instrument'] = relationship()
