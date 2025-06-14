from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories import InstrumentRepository
from app.data.models import Instrument
from app.domain.entities import InstrumentCreate, InstrumentResponse
from app.api.exceptions.exceptions import NotFoundException


class InstrumentService:
    def __init__(
        self,
        session: AsyncSession,
        instrument_repo: InstrumentRepository,
    ):
        self.session = session
        self.instrument_repo = instrument_repo

    async def create_instrument(self, instrument: InstrumentCreate) -> InstrumentResponse:
        instrument_dict = instrument.model_dump()
        instrument_obj = Instrument(**instrument_dict)

        # TODO handle ticker collision

        await self.instrument_repo.add(obj=instrument_obj)
        response = InstrumentResponse.model_validate(instrument_obj)

        await self.session.commit()

        return response

    async def get_all_instruments(self) -> list[InstrumentResponse]:
        instruments = await self.instrument_repo.get_all()
        return [InstrumentResponse.model_validate(instrument) for instrument in instruments]

    async def delete_instument_by_ticker(self, ticker: str) -> None:
        instrument = await self.instrument_repo.get_instrument_by_ticker(ticker=ticker)

        if not instrument:
            raise NotFoundException(entity_name='Instrument')

        deleted_instrument = await self.instrument_repo.delete(obj=instrument)
        await self.session.commit()
        return deleted_instrument
