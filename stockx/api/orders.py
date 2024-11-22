from datetime import datetime
from typing import AsyncIterator

from .base import StockXAPIBase
from ..format import iso_date
from ..models import OrderDetail, Order


class Orders(StockXAPIBase):
    
    async def get_order(
            self, 
            order_number: str
    ) -> OrderDetail:
        response = await self.client.get(f'/selling/orders/{order_number}')
        return OrderDetail.from_json(response.data)

    async def get_orders_history(
            self,
            from_date: datetime = None,
            to_date: datetime = None,
            order_status: str = None,
            product_id: str = None,
            variant_id: str = None, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[Order]:
        params = {
            'fromDate': iso_date(from_date),
            'toDate': iso_date(to_date),
            'orderStatus': order_status,
            'productId': product_id,
            'variantId': variant_id
        }
        async for order in self._page(
            endpoint='/selling/orders/history',
            results_key='orders',
            params=params,
            limit=limit,
            page_size=page_size
        ):
            yield Order.from_json(order)

    async def get_active_orders(
            self,
            order_status: str = None,
            product_id: str = None,
            variant_id: str = None,
            sort_order: str = None, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[Order]:
        params = {
            'orderStatus': order_status,
            'productId': product_id,
            'variantId': variant_id,
            'sortOrder': sort_order
        }
        async for order in self._page(
            endpoint='/selling/orders/active',
            results_key='orders',
            params=params,
            limit=limit,
            page_size=page_size
        ):
            yield Order.from_json(order)