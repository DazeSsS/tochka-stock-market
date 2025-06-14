from enum import Enum


class OrderType(str, Enum):
    LIMIT = 'LIMIT'
    MARKET = 'MARKET'


class OrderStatus(str, Enum):
    NEW = 'NEW'
    EXECUTED = 'EXECUTED'
    PARTIALLY_EXECUTED = 'PARTIALLY_EXECUTED'
    CANCELLED = 'CANCELLED'


class OrderDirection(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'
