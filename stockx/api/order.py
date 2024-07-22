from typing import AsyncIterator

from stockx.models import (
    Product, 
    Variant, 
    MarketData
)

from stockx.api.base import StockXAPI


class Order(StockXAPI):
    pass