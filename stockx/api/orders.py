from collections.abc import AsyncIterator
from datetime import datetime

from .base import StockXAPIBase
from ..format import iso_date
from ..models import Order, OrderDetail


class Orders(StockXAPIBase):
    """Interface for interacting with sales orders."""

    async def get_order(
            self, 
            order_number: str
    ) -> OrderDetail:
        """Get a sales order by its number."""
        response = await self.client.get(f'/selling/orders/{order_number}')
        return OrderDetail.from_json(response.data)

    async def get_orders_history(
            self,
            from_date: datetime | None = None,
            to_date: datetime | None = None,
            order_status: str | None = None,
            product_id: str | None = None,
            variant_id: str | None = None, 
            limit: int | None = None, 
            page_size: int = 10
    ) -> AsyncIterator[Order]:
        """Get the history of completed sales orders."""
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
            order_status: str | None = None,
            product_id: str | None = None,
            variant_id: str | None = None,
            sort_order: str | None = None, 
            limit: int | None = None, 
            page_size: int = 10
    ) -> AsyncIterator[Order]:
        """Get currently active sales orders."""
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