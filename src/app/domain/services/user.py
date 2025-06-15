import uuid
from utils import generate_api_key
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories import BalanceRepository, InstrumentRepository, UserRepository, WalletRepository
from app.data.models import Balance, Instrument, User, Wallet
from app.domain.entities import UserCreate, UserResponse
from app.domain.enums import UserRole
from app.api.exceptions.exceptions import NotFoundException


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        balance_repo: BalanceRepository,
        instrument_repo: InstrumentRepository,
        user_repo: UserRepository,
        wallet_repo: WalletRepository,
    ):
        self.session = session
        self.balance_repo = balance_repo
        self.instrument_repo = instrument_repo
        self.user_repo = user_repo
        self.wallet_repo = wallet_repo

    async def create_user(self, user: UserCreate) -> UserResponse:
        user_dict = user.model_dump()
        user_obj = User(**user_dict)

        user_obj.role = UserRole.USER
        user_obj.api_key = generate_api_key()

        async with self.session.begin():
            await self.user_repo.add(obj=user_obj)

            user_wallet = Wallet(user_id=user_obj.id)
            await self.wallet_repo.add(obj=user_wallet)
            
            rub_instrument = await self.instrument_repo.get_instrument_by_ticker(ticker='RUB')
            if not rub_instrument:
                rub_instrument = Instrument(name='Ruble', ticker='RUB')
                await self.instrument_repo.add(rub_instrument)

            user_rub_balance = Balance(
                wallet_id=user_wallet.id,
                instrument_id=rub_instrument.id
            )
            await self.balance_repo.add(user_rub_balance)

            return UserResponse.model_validate(user_obj)

    async def get_user_by_api_key(self, api_key: str) -> UserResponse:
        user = await self.user_repo.get_user_by_api_key(api_key=api_key)

        if not user:
            raise NotFoundException(entity_name='User')

        return UserResponse.model_validate(user)

    async def delete_user_by_id(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(id=user_id)

        if not user:
            raise NotFoundException(entity_name='User')

        deleted_user = await self.user_repo.delete(obj=user)
        await self.session.commit()
        return deleted_user
