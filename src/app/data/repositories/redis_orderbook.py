import uuid
import time
from redis.asyncio import Redis

from config import settings
from app.domain.enums import OrderDirection, OrderStatus


class OrderBookRepository:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def add_order(
        self,
        order_id: str,
        ticker: str,
        direction: OrderDirection,
        price: int,
        qty: int,
        user_id: str,
    ):
        timestamp = time.time()
        pipe = self.redis.pipeline()
        
        pipe.zadd(
            f'orderbook:{ticker}:{direction.value}',
            {order_id: price}
        )
        
        pipe.hset(
            f'order:{order_id}',
            mapping={
                'ticker': ticker,
                'direction': direction,
                'price': str(price),
                'qty': str(qty),
                'filled': '0',
                'user_id': user_id,
                'status': OrderStatus.NEW,
                'timestamp': str(timestamp)
            }
        )
        
        await pipe.execute()

    async def find_matches(
        self,
        ticker: str,
        direction: OrderDirection,
        price: int
    ) -> list[tuple[str, int]]:
        opposite_dir = OrderDirection.SELL if direction == OrderDirection.BUY else OrderDirection.BUY
        key = f'orderbook:{ticker}:{opposite_dir.value}'
        
        if direction == OrderDirection.BUY:
            # Для покупки: цена в стакане <= нашей цене (ищем самые дешевые предложения)
            if price == 0:  # Рыночная заявка - берем лучшее предложение
                orders = await self.redis.zrange(key, 0, -1, withscores=True)
            else:
                orders = await self.redis.zrangebyscore(
                    key, min=0, max=price, withscores=True
                )
        else:
            # Для продажи: цена в стакане >= нашей цене (ищем самые дорогие предложения)
            if price == 0:  # Рыночная заявка - берем лучшее предложение
                orders = await self.redis.zrevrange(key, 0, 0, withscores=True)
            else:
                orders = await self.redis.zrangebyscore(
                    key, min=price, max='+inf', withscores=True
                )
        
        # Сортируем по времени добавления (FIFO)
        if orders:
            # Получаем timestamp для каждого ордера
            pipe = self.redis.pipeline()
            for order_id, _ in orders:
                pipe.hget(f'order:{order_id}', 'timestamp')
            timestamps = await pipe.execute()
            
            # Сортируем по timestamp
            sorted_orders = sorted(
                zip(orders, timestamps),
                key=lambda x: float(x[1])
            )
            return [(order_id, float(score)) for (order_id, score), _ in sorted_orders]
        return []

    async def update_order_status(self, order_id: str, status: OrderStatus):
        await self.redis.hset(
            f'order:{order_id}', 'status', status.value
        )

    async def get_price_levels(
        self,
        ticker: str,
        direction: OrderDirection,
        limit: int
    ) -> dict[int, int]:
        """Получает агрегированные уровни цен для заданного направления"""
        key = f'orderbook:{ticker}:{direction.value}'
        
        # Для покупки берем самые высокие цены, для продажи - самые низкие
        if direction == OrderDirection.BUY:
            orders = await self.redis.zrevrange(key, 0, limit - 1, withscores=True)
        else:
            orders = await self.redis.zrange(key, 0, limit - 1, withscores=True)
        
        # Агрегируем объемы по ценам
        price_levels = {}
        for order_id, price in orders:
            order_data = await self.get_order_data(order_id)
            if order_data:
                qty = int(order_data['qty']) - int(order_data['filled'])
                if qty > 0:
                    price = int(price)
                    if price in price_levels:
                        price_levels[price] += qty
                    else:
                        price_levels[price] = qty
        
        return price_levels

    async def get_best_price(
        self,
        ticker: str,
        direction: str
    ) -> int | None:
        key = f'orderbook:{ticker}:{'SELL' if direction == 'BUY' else 'BUY'}'
        
        if direction == 'BUY':
            result = await self.redis.zrange(
                key, start=0, end=0, withscores=True
            )
        else:
            result = await self.redis.zrevrange(
                key, start=0, end=0, withscores=True
            )
            
        return result[0][1] if result else None

    async def _get_next_best_price(self, ticker: str, direction: OrderDirection) -> int | None:
        """Получаем следующую лучшую цену после частичного исполнения"""
        opposite_dir = OrderDirection.SELL if direction == OrderDirection.BUY else OrderDirection.BUY
        key = f'orderbook:{ticker}:{opposite_dir.value}'
        
        if direction == OrderDirection.BUY:
            # Берем вторую минимальную цену
            results = await self.redis.zrange(key, 1, 1, withscores=True)
        else:
            # Берем вторую максимальную цену
            results = await self.redis.zrevrange(key, 1, 1, withscores=True)
        
        return results[0][1] if results else None

    async def get_order_data(
        self,
        order_id: str
    ) -> dict[str, str] | None:
        return await self.redis.hgetall(f'order:{order_id}')

    async def update_order_fill(
        self,
        order_id: str,
        fill_qty: int
    ):
        await self.redis.hincrbyfloat(
            f'order:{order_id}', 'filled', fill_qty
        )

    async def remove_order(
        self,
        order_id: str
    ):
        data = await self.get_order_data(order_id)
        if not data:
            return
            
        pipe = self.redis.pipeline()
        pipe.zrem(
            f'orderbook:{data['ticker']}:{data['direction']}',
            order_id
        )
        
        pipe.delete(f'order:{order_id}')
        
        await pipe.execute()
