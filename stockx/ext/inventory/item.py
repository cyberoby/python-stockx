from __future__ import annotations

from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .inventory import Inventory

from ...api import StockX
from ...models import Listing


@dataclass
class ItemMarketData:
    lowest_ask: float
    highest_bid: float
    earn_more: float
    flex_lowest_ask: float

    
class Item:
    
    __slots__ = (
        'variant_id', 
        'price', 
        'quantity'
        'product_id'
        '_style_id', 
        '_size',
    )

    def __init__(
            self,
            product_id: str,
            variant_id: str,
            price: float,
            quantity: int,
    ) -> None:
        self.product_id = product_id
        self.variant_id = variant_id
        self.price = price
        self.quantity = quantity
        self.listing_ids: list[str] = []
        self._inventory: Inventory | None = None

        self.__style_id = None
        self.__size = None

    @classmethod
    async def from_listings(
            cls, 
            listings: AsyncIterable[Listing]
    ) -> list[Item]:
        items: dict[str, dict[float, Item]] = {}

        async for listing in listings:
            amounts_dict = items.setdefault(listing.variant.id, {})
            
            if listing.amount in amounts_dict:
                amounts_dict[listing.amount].quantity += 1
                amounts_dict[listing.amount].listing_ids.append(listing.id)
            else:
                item = Item(
                    product_id=listing.product.id,
                    variant_id=listing.variant.id,
                    price=listing.amount,
                    quantity=1,
                )
                item.listing_ids.append(listing.id)
                item.__style_id = listing.style_id
                item.__size = listing.variant_value

                amounts_dict[listing.amount] = item

        return [
            inventory_item 
            for amount in items.values() 
            for inventory_item in amount.values()
        ]
    
    @property
    def price(self) -> float:
        return self.__price
    
    @price.setter
    def price(self, value: float) -> None:
        if value != self.__price:
            self.__price = value
            if self._inventory:
                self._inventory.register_price_change(self)
    
    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if value < 0:
            raise ValueError("Quantity can't be negative.")
        
        if int(value) != value:
            raise ValueError('Quantity must be an integer.')
            
        if value != self._quantity:
            self._quantity = value
            if self._inventory:
                self._inventory.register_quantity_change(self)

    @property
    def style_id(self) -> str:
        if self.__style_id:
            return self.__style_id
        else:
            raise AttributeError(
                'Style ID is not available. '
                'Fetch it first using `await fetch_style_id()`'
            )
    
    @property
    def size(self) -> str:
        if self.__size:
            return self.__size
        else:
            raise AttributeError(
                'Size is not available. '
                'Fetch it first using `await fetch_size()`'
            )
    
    def quantity_to_sync(self) -> int:
        return self.quantity - len(self.listing_ids)
    
    def payout(self) -> float: # TODO: compute payout based on active orders
        if self._inventory:
            transaction_fee = max(
                self._inventory.transaction_fee * self.price, 
                self._inventory.minimum_transaction_fee
            )
            payment_fee = self._inventory.payment_fee * self.price
            shipping_fee = self._inventory.shipping_fee
            return self.price - transaction_fee - payment_fee - shipping_fee 
        else:
            raise # what?

    async def fetch_size(self, stockx: StockX) -> str:
        await stockx.catalog.get_product_variant(self.product_id, self.variant_id)