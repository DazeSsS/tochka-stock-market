import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.data.repositories import (
    BalanceRepository,
    InstrumentRepository,
    OrderBookRepository,
    OrderRepository,
    TransactionRepository,
    WalletRepository,
)
from app.data.models import Balance, Order, Transaction
from app.domain.entities import (
    LimitOrderCreate,
    LimitOrderResponse,
    LevelsResponse,
    MarketOrderCreate,
    MarketOrderResponse,
    OrderBookResponse,
    SuccessOrderResponse
)
from app.domain.enums import OrderDirection, OrderStatus, OrderType
from app.api.exceptions.exceptions import NotFoundException
from app.api.exceptions.schemas import SuccessResponse


class OrderService:
    def __init__(
        self,
        session: AsyncSession,
        balance_repo: BalanceRepository,
        instrument_repo: InstrumentRepository,
        order_repo: OrderRepository,
        orderbook: OrderBookRepository,
        transaction_repo: TransactionRepository,
        wallet_repo: WalletRepository,
    ):
        self.session = session
        self.balance_repo = balance_repo
        self.instrument_repo = instrument_repo
        self.order_repo = order_repo
        self.orderbook = orderbook
        self.transaction_repo = transaction_repo
        self.wallet_repo = wallet_repo

    async def list_orders(self, user_id: uuid.UUID) -> list[LimitOrderResponse | MarketOrderResponse]:
        user_orders = await self.order_repo.get_user_orders(user_id=user_id)

        result_orders = []
        for order in user_orders:
            if order.order_type == OrderType.LIMIT:
                limit_order = await self._get_limit_order_response(order)
                result_orders.append(limit_order)
            else:
                limit_order = await self._get_market_order_response(order)
                result_orders.append(limit_order)
        
        return result_orders

    async def get_order_by_id(self, user_id: uuid.UUID, order_id: uuid.UUID) -> LimitOrderResponse | MarketOrderResponse:
        user_order = await self.order_repo.get_by_id(order_id)

        if user_order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Can't get other user's order")

        if user_order.order_type == OrderType.LIMIT:
            return await self._get_limit_order_response(user_order)
        else:
            return await self._get_market_order_response(user_order)

    async def get_orderbook(self, ticker: str, limit: int) -> OrderBookResponse:
        buy_orders = await self.orderbook.get_price_levels(ticker, OrderDirection.BUY, limit)
        sell_orders = await self.orderbook.get_price_levels(ticker, OrderDirection.SELL, limit)
        
        bid_levels = []
        ask_levels = []
        
        for price, qty in sorted(buy_orders.items(), reverse=True):
            bid_levels.append(LevelsResponse(price=price, qty=qty))
        
        for price, qty in sorted(sell_orders.items()):
            ask_levels.append(LevelsResponse(price=price, qty=qty))
        
        return OrderBookResponse(bid_levels=bid_levels, ask_levels=ask_levels)

    async def _get_limit_order_response(self, order: Order) -> LimitOrderResponse:
        instrument = await self.instrument_repo.get_by_id(order.instrument_id)
        return LimitOrderResponse(
            id=order.id,
            status=order.status,
            user_id=order.user_id,
            timestamp=order.timestamp,
            body=LimitOrderCreate(
                direction=order.direction,
                ticker=instrument.ticker,
                qty=order.qty,
                price=order.price
            ),
            filled=order.filled
        )

    async def _get_market_order_response(self, order: Order) -> MarketOrderResponse:
        instrument = await self.instrument_repo.get_by_id(order.instrument_id)
        return MarketOrderResponse(
            id=order.id,
            status=order.status,
            user_id=order.user_id,
            timestamp=order.timestamp,
            body=MarketOrderCreate(
                direction=order.direction,
                ticker=instrument.ticker,
                qty=order.qty
            )
        )

    async def create_order(self, user_id: uuid.UUID, order: LimitOrderCreate | MarketOrderCreate) -> SuccessOrderResponse:
        async with self.session.begin():
            instrument = await self.instrument_repo.get_instrument_by_ticker(ticker=order.ticker)
            if not instrument:
                raise HTTPException(status_code=404, detail="Instrument not found")

            wallet = await self.wallet_repo.get_wallet_by_user_id(user_id=user_id)
            if not wallet:
                raise HTTPException(status_code=404, detail="Wallet not found")

            rub_instrument = await self.instrument_repo.get_instrument_by_ticker(ticker="RUB")
            if not rub_instrument:
                raise HTTPException(status_code=404, detail="RUB instrument not configured")

            if isinstance(order, LimitOrderCreate):
                if order.direction == OrderDirection.BUY:
                    required_amount = order.qty * order.price

                    balance = await self.balance_repo.get_user_balance_of_instrument(wallet.id, rub_instrument.id)
                    if not balance or balance.amount < required_amount:
                        raise HTTPException(status_code=400, detail="Insufficient RUB quantity")

                    await self._reserve_funds(wallet.id, rub_instrument.id, required_amount)
                else:
                    balance = await self.balance_repo.get_user_balance_of_instrument(wallet.id, instrument.id)
                    if not balance or balance.amount < order.qty:
                        raise HTTPException(status_code=400, detail="Insufficient instrument quantity")

                    await self._reserve_funds(wallet.id, instrument.id, order.qty)
            else:
                if order.direction == OrderDirection.BUY:
                    total_cost = await self._calculate_market_buy_cost(order.ticker, order.qty)
                    if total_cost is None:
                        raise HTTPException(status_code=400, detail="Not enough liquidity for market order")

                    balance = await self.balance_repo.get_user_balance_of_instrument(wallet.id, rub_instrument.id)
                    if not balance or balance.amount < total_cost:
                        raise HTTPException(status_code=400, detail="Insufficient RUB quantity")
                else:
                    balance = await self.balance_repo.get_user_balance_of_instrument(wallet.id, instrument.id)
                    if not balance or balance.amount < order.qty:
                        raise HTTPException(status_code=400, detail="Insufficient instrument quantity")

            order_obj = Order(
                user_id=user_id,
                instrument_id=instrument.id,
                order_type=OrderType.LIMIT if isinstance(order, LimitOrderCreate) else OrderType.MARKET,
                status=OrderStatus.NEW,
                direction=order.direction,
                qty=order.qty,
                price=order.price if isinstance(order, LimitOrderCreate) else 0,
                filled=0
            )
            await self.order_repo.add(order_obj)

            if isinstance(order, LimitOrderCreate):
                await self.orderbook.add_order(
                    order_id=str(order_obj.id),
                    ticker=order.ticker,
                    direction=order.direction,
                    price=order.price,
                    qty=order.qty,
                    user_id=str(user_id),
                )

                await self._try_execute_order(
                    order_id=str(order_obj.id),
                    ticker=order.ticker,
                    direction=order.direction,
                    price=order.price,
                    order_type=OrderType.LIMIT
                )
            else:
                await self._try_execute_order(
                    order_id=str(order_obj.id),
                    ticker=order.ticker,
                    direction=order.direction,
                    price=0,
                    order_type=OrderType.MARKET
                )

            return SuccessOrderResponse(order_id=order_obj.id)

    async def _calculate_market_buy_cost(self, ticker: str, qty: int) -> int | None:
        total_cost = 0
        remaining_qty = qty
        
        sell_orders = await self.orderbook.find_matches(ticker, OrderDirection.BUY, 0)
        
        for order_id, order_price in sell_orders:
            if remaining_qty <= 0:
                break

            order = await self.orderbook.get_order_data(order_id)
            
            available_qty = int(order['qty']) - int(order['filled'])
            fill_qty = min(available_qty, remaining_qty)
            total_cost += fill_qty * order_price
            remaining_qty -= fill_qty
        
        return total_cost if remaining_qty == 0 else None

    async def _reserve_funds(self, wallet_id: int, instrument_id: int, amount: int):
        balance = await self.balance_repo.get_user_balance_of_instrument(wallet_id, instrument_id)
        if not balance or balance.amount < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        await self.balance_repo.reserve(wallet_id, instrument_id, amount)

    async def _release_funds(self, wallet_id: int, instrument_id: int, amount: int):
        await self.balance_repo.release(wallet_id, instrument_id, amount)

    async def _transfer_funds(self, from_wallet_id: int, to_wallet_id: int, 
                            instrument_id: int, amount: int):
        await self.balance_repo.transfer(
            from_wallet_id, to_wallet_id, instrument_id, amount
        )

    async def _try_execute_order(
        self, 
        order_id: str, 
        ticker: str, 
        direction: OrderDirection, 
        price: int,
        order_type: OrderType
    ):
        if order_type == OrderType.LIMIT:
            order_data = await self.orderbook.get_order_data(order_id)
            remaining_qty = int(order_data['qty']) - int(order_data['filled'])
        else:
            order = await self.order_repo.get_by_id(order_id)
            remaining_qty = order.qty - order.filled

        while remaining_qty > 0:
            matches = await self.orderbook.find_matches(ticker, direction, float(price))
            
            if not matches:
                break

            for match_id, match_price in matches:
                match_price = min(match_price, price)
                if remaining_qty <= 0:
                    break
            
                executed_qty = await self._execute_trade(
                    order_id=order_id,
                    match_id=match_id,
                    ticker=ticker,
                    price=match_price,
                    order_type=order_type,
                    max_qty=remaining_qty
                )

                remaining_qty -= executed_qty

    async def _execute_trade(
        self,
        order_id: str,
        match_id: str,
        ticker: str,
        price: int,
        order_type: OrderType,
        max_qty: int,
    ) -> int:
        if order_type == OrderType.LIMIT:
            order_data = await self.orderbook.get_order_data(order_id)
            order_qty = int(order_data['qty'])
            order_filled = int(order_data['filled'])
            order_direction = order_data['direction']
            order_status = order_data['status']
            order_price = int(order_data['price'])
            order_user_id = order_data['user_id']
        else:
            order_data = await self.order_repo.get_by_id(order_id)
            order_qty = order_data.qty
            order_filled = order_data.filled
            order_direction = order_data.direction
            order_status = order_data.status
            order_price = order_data.price
            order_user_id = order_data.user_id

        match_data = await self.orderbook.get_order_data(match_id)
        match_qty = int(match_data['qty'])
        match_filled = int(match_data['filled'])
        match_direction = match_data['direction']
        match_price = int(match_data['price'])
        match_user_id = match_data['user_id']
        
        if not order_data or not match_data or order_status not in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            return False

        order_remaining = order_qty - order_filled
        match_remaining = match_qty - match_filled
        fill_qty = min(order_remaining, match_remaining)
        
        if fill_qty <= 0:
            return 0

        instrument = await self.instrument_repo.get_instrument_by_ticker(ticker)
        rub_instrument = await self.instrument_repo.get_instrument_by_ticker("RUB")
        
        order_wallet = await self.wallet_repo.get_wallet_by_user_id(order_user_id)
        match_wallet = await self.wallet_repo.get_wallet_by_user_id(match_user_id)

        if order_type == OrderType.LIMIT:
            if order_direction == OrderDirection.BUY:
                await self.balance_repo.release(
                    order_wallet.id, 
                    rub_instrument.id,
                    fill_qty * order_price
                )
            else:
                await self.balance_repo.release(
                    order_wallet.id,
                    instrument.id,
                    fill_qty
                )

        if match_direction == OrderDirection.BUY:
            buyer_wallet = match_wallet
            seller_wallet = order_wallet

            await self.balance_repo.release(
                match_wallet.id,
                rub_instrument.id,
                fill_qty * match_price
            )
        else:
            buyer_wallet = order_wallet
            seller_wallet = match_wallet

            await self.balance_repo.release(
                match_wallet.id,
                instrument.id,
                fill_qty
            )

        await self._transfer_funds(
            seller_wallet.id, buyer_wallet.id, instrument.id, fill_qty)

        rub_amount = fill_qty * price
        await self._transfer_funds(
            buyer_wallet.id, seller_wallet.id, rub_instrument.id, rub_amount)

        transaction_obj = Transaction(
            instrument_id=instrument.id,
            wallet_id=seller_wallet.id,
            amount=fill_qty,
            price=price,
        )
        await self.transaction_repo.add(transaction_obj)

        await self._update_order_fills(order_id, order_type, match_id, fill_qty)

        return fill_qty

    async def _update_order_fills(self, order_id: uuid.UUID, order_type: OrderType, match_id: str, fill_qty: int):
        order_status = await self.order_repo.update_filled(order_id=order_id, fill_qty=fill_qty)
        match_status = await self.order_repo.update_filled(order_id=match_id, fill_qty=fill_qty)
        
        if order_type == OrderType.LIMIT:
            await self.orderbook.update_order_fill(order_id, fill_qty)
            await self.orderbook.update_order_status(order_id, order_status)
            if order_status == OrderStatus.EXECUTED:
                await self.orderbook.remove_order(order_id)

        await self.orderbook.update_order_fill(match_id, fill_qty)
        await self.orderbook.update_order_status(match_id, match_status)
        if match_status == OrderStatus.EXECUTED:
            await self.orderbook.remove_order(match_id)

    async def cancel_order(self, order_id: uuid.UUID, user_id: uuid.UUID) -> SuccessResponse:
        async with self.session.begin():
            order = await self.order_repo.get_by_id(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            if order.order_type == OrderType.MARKET:
                raise HTTPException(status_code=400, detail="Can't cancel market order")
            
            if order.user_id != user_id:
                raise HTTPException(status_code=403, detail="Can't cancel other user's order")
            
            if order.status not in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
                raise HTTPException(status_code=400, detail="Can't cancel executed or cancelled order")

            wallet = await self.wallet_repo.get_wallet_by_user_id(user_id)
            if order.direction == OrderDirection.BUY:
                rub_instrument = await self.instrument_repo.get_instrument_by_ticker("RUB")
                reserved_amount = (order.qty - order.filled) * order.price
                await self._release_funds(wallet.id, rub_instrument.id, reserved_amount)
            else:
                reserved_amount = order.qty - order.filled
                await self._release_funds(wallet.id, order.instrument_id, reserved_amount)

            await self.order_repo.update_status(order_id=order_id, status=OrderStatus.CANCELLED)
            
            if order.order_type == OrderType.LIMIT:
                await self.orderbook.remove_order(str(order_id))

            return SuccessResponse()
