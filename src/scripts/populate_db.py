import asyncio
from utils import generate_api_key

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from config import settings
from app.data.models import Balance, Instrument, User, Wallet
from app.domain.enums import UserRole

DATABASE_URL = settings.get_db_url()

engine = create_async_engine(DATABASE_URL)


async def initialize(session: AsyncSession):
    async with session.begin():

        # Создание пользователей

        admin_api_key = generate_api_key()
        admin_user = User(
            name='Ivan',
            role=UserRole.ADMIN,
            api_key=admin_api_key,
        )
        session.add(admin_user)
        await session.flush()
        admin_wallet = Wallet(user_id=admin_user.id)
        session.add(admin_wallet)

        print('Admin id:', admin_user.id)
        print('Admin token: TOKEN', admin_api_key)

        print()

        api_key = generate_api_key()
        user = User(
            name='Vlad',
            role=UserRole.USER,
            api_key=api_key,
        )
        session.add(user)
        await session.flush()
        user_wallet = Wallet(user_id=user.id)
        session.add(user_wallet)

        print('User id:', user.id)
        print('User token: TOKEN', api_key)


        # Создание инструментов

        rub_obj = Instrument(
            ticker='RUB',
            name='Ruble'
        )
        btc_obj = Instrument(
            ticker='BTC',
            name='Bitcoin'
        )

        session.add(rub_obj)
        session.add(btc_obj)
        await session.flush()


        # Начисление начального баланса

        admin_rub_balance = Balance(
            wallet_id=admin_wallet.id,
            instrument_id=rub_obj.id,
            amount=100
        )
        user_btc_balance = Balance(
            wallet_id=user_wallet.id,
            instrument_id=btc_obj.id,
            amount=2
        )
        session.add(admin_rub_balance)
        session.add(user_btc_balance)


async def populate_db():
    async with AsyncSession(engine) as session:
        await initialize(session)

if __name__ == '__main__':
    asyncio.run(populate_db())
