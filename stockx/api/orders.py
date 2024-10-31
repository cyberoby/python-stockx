from datetime import datetime
from typing import AsyncIterator

from stockx.api.base import StockXAPIBase
from stockx.models.core import Order, OrderPartial


class Orders(StockXAPIBase):
    
    async def get_order(
            self, 
            order_number: str
    ) -> Order:
        response = await self.client.get(f'/selling/orders/{order_number}')
        return Order.from_json(response.data)

    async def get_orders_history(
            self,
            from_date: datetime = None,
            to_date: datetime = None,
            order_status: str = None,
            product_id: str = None,
            variant_id: str = None, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[OrderPartial]:
        params = {
            'fromDate': str(datetime.date(from_date)) if from_date else None,
            'toDate': str(datetime.date(to_date)) if to_date else None,
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
            yield OrderPartial.from_json(order)

    async def get_active_orders(
            self,
            order_status: str = None,
            product_id: str = None,
            variant_id: str = None,
            sort_order: str = None, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[OrderPartial]:
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
            yield OrderPartial.from_json(order)