from collections.abc import Iterator

from .batch.operations import (
    UpdateResult,
    update_listings, 
    update_quantity,
)
from .item import ListedItem
from .query import create_items_query, ItemsQuery
from ..mock import mock_listing
from ...api import StockX


class Inventory:

    __slots__ = (
        '_price_updates',
        '_quantity_updates',
        'currency',
        'minimum_transaction_fee',
        'payment_fee',
        'shipping_fee',
        'stockx',
        'transaction_fee',
    )

    def __init__(
            self, 
            stockx: StockX, 
            currency = 'EUR', 
            shipping_fee = 7,
            minimum_transaction_fee = 5,
    ) -> None:
        self.stockx = stockx
        self.currency = currency
        self.shipping_fee = shipping_fee
        self.minimum_transaction_fee = minimum_transaction_fee

        self.transaction_fee = 0.09
        self.payment_fee = 0.03

        self._price_updates: set[ListedItem] = set()
        self._quantity_updates: set[ListedItem] = set()

    def register_price_change(self, item: ListedItem) -> None:
        self._price_updates.add(item)

    def register_quantity_change(self, item: ListedItem) -> None:
        self._quantity_updates.add(item)

    def items(self) -> ItemsQuery:
        return create_items_query(self)

    async def load(self) -> None:
        await self.load_fees()

    async def load_fees(self) -> None:
        async for listing in self.stockx.listings.get_all_listings(
            listing_statuses='ACTIVE',
            limit=100,
            page_size=100,
        ):
            detail = await self.stockx.listings.get_listing(listing.id)
            if detail.payout:
                self.transaction_fee = detail.payout.transaction_fee
                self.payment_fee = detail.payout.payment_fee
                return
        
        async with mock_listing(
            stockx=self.stockx, 
            currency_code=self.currency
        ) as detail:
            if detail and detail.payout:
                self.transaction_fee = detail.payout.transaction_fee
                self.payment_fee = detail.payout.payment_fee
                return
        
        raise RuntimeError('Unable to load fees. Level 1 fees applied.')
    
    async def update(self) -> Iterator[UpdateResult]:
        quantity_results = await update_quantity(self._quantity_updates)
        price_results = await update_listings(self._price_updates)

        self._price_updates.clear()
        self._quantity_updates.clear()

        return UpdateResult.consolidate(quantity_results, price_results)
    

