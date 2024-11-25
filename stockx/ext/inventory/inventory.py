from __future__ import annotations
from collections.abc import (
    Awaitable,
    Callable,
    Iterable, 
    Iterator,
)
from typing import TYPE_CHECKING, TypeVar

from .batch.operations import (
    UpdateResult,
    publish_listings,
    update_listings, 
    update_quantity,
)
from .item import ListedItem
from .market import create_item_market_data
from .query import create_items_query
from ..mock import mock_listing
from ...api import StockX

if TYPE_CHECKING:
    from .market import ItemMarketData, MarketValue
    from .query import ItemsQuery


I = TypeVar('I')
O = TypeVar('O')

type ComputedValue[I, O] = O | Callable[[I], O] | Callable[[I], Awaitable[O]]

Amount = ComputedValue[ListedItem, float]
Condition = ComputedValue[ListedItem, bool]


async def computed_value(input: I, value: ComputedValue[I, O]) -> O:
    if callable(value):
        try:
            return await value(input)
        except TypeError:
                return value(input)
    else:
        return value


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
            currency: str = 'EUR',  # TODO: enum?
            shipping_fee: float = 7.0,
            minimum_transaction_fee: float = 5.0,
            transaction_fee_percentage: float = 0.09,
            payment_fee_percentage: float = 0.03
    ) -> None:
        self.stockx = stockx
        self.currency = currency
        self.shipping_fee = shipping_fee
        self.minimum_transaction_fee = minimum_transaction_fee
        self.transaction_fee = transaction_fee_percentage
        self.payment_fee = payment_fee_percentage

        self._price_updates: set[ListedItem] = set()
        self._quantity_updates: set[ListedItem] = set()

    async def __aenter__(self) -> Inventory:
        await self.load()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        results = await self.update()
        for result in results:
            print(result)
        # TODO: return True and suppress exc?

    async def load(self) -> None:
        await self.load_fees()

    async def load_fees(self) -> None:
        async for listing in self.stockx.listings.get_all_listings(
            listing_statuses=['ACTIVE'],
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
    
    def items(self) -> ItemsQuery:
        return create_items_query(self)
    
    async def get_item_market_data(
            self, 
            item: ListedItem | ListedItem
    ) -> ItemMarketData:
        market_data = await self.stockx.catalog.get_product_market_data(
            product_id=item.product_id, 
            currency_code=self.currency
        )

        variant_market_data_set = set(market_data)
        variant_market_data = next(
            data for data in variant_market_data_set 
            if data.variant_id == item.variant_id
        )
        
        return create_item_market_data(
            market_data=variant_market_data, 
            payout_calculator=self.calculate_payout, 
            currency=self.currency
        )
    
    def calculate_payout(self, amount: float) -> float:  # TODO: compute payout based on active orders
        transaction_fee = max(
            self.transaction_fee * amount,  
            self.minimum_transaction_fee
        )
        return (
            amount 
            - transaction_fee 
            - self.payment_fee * amount 
            - self.shipping_fee
        )
    
    def register_price_change(self, item: ListedItem) -> None:
        self._price_updates.add(item)

    def register_quantity_change(self, item: ListedItem) -> None:
        self._quantity_updates.add(item)

    async def update(self) -> Iterator[UpdateResult]:
        quantity_results, price_results = [], []
        if self._quantity_updates:
            for item in self._quantity_updates:
                print(f'{item.name=}')
                print(f'{item.size=}')
                print(f'{item.quantity=}')
                print(f'{item.quantity_to_sync()=}')
                print(f'{item.payout()=}')
            quantity_results = await update_quantity(
                stockx=self.stockx, 
                items=self._quantity_updates
            )
        if self._price_updates:
            print('price')
            price_results = await update_listings(
                stockx=self.stockx, 
                items=self._price_updates
            )

        self._price_updates.clear()
        self._quantity_updates.clear()

        return UpdateResult.consolidate(quantity_results, price_results)
    
    async def sell(self, items: Iterable[ListedItem]) -> list[ListedItem]:
        results = await publish_listings(self.stockx, items)
        return [
            ListedItem(
                item=result.item, 
                inventory=self, 
                listing_ids=result.created
            )
            for result in results
            if result.created
        ]

    async def beat_lowest_ask(
            self,
            items: Iterable[ListedItem], 
            beat_by: Amount = 1,
            percentage: bool = False,
            condition: Condition = True,
    ):
        return await self._beat_market_value(
            items=items, 
            get_market_value=lambda m: m.lowest_ask, 
            beat_by=beat_by, 
            condition=condition, 
            percentage=percentage
        )

    async def beat_sell_faster(
            self,
            items: Iterable[ListedItem], 
            beat_by: Amount = 0,
            percentage: bool = False,
            condition: Condition = True,
    ):
        return await self._beat_market_value(
            items=items, 
            get_market_value=lambda m: m.sell_faster, 
            beat_by=beat_by, 
            condition=condition, 
            percentage=percentage
        )

    async def beat_earn_more(
            self,
            items: Iterable[ListedItem], 
            beat_by: Amount = 0,
            percentage: bool = False,
            condition: Condition = True,
    ):
        return await self._beat_market_value(
            items=items, 
            get_market_value=lambda m: m.earn_more, 
            beat_by=beat_by, 
            condition=condition, 
            percentage=percentage
        )
    
    async def change_price(
            self,
            items: Iterable[ListedItem],
            new_price: Amount,
            condition: Condition = True,
    ):
        items_to_update = [
            item for item in items 
            if await computed_value(item, condition)
        ]

        for item in items_to_update:
            item.price = await computed_value(item, new_price)

        await update_listings(self.stockx, items_to_update)
    
        self._price_updates.difference_update(items_to_update)
    
    async def _beat_market_value(
            self,
            items: Iterable[ListedItem], 
            get_market_value: Callable[[ItemMarketData], MarketValue | None],
            beat_by: Amount,
            percentage: bool,
            condition: Condition,
    ):
        async def new_price(item):
            change = await computed_value(item, beat_by)
            
            market_data = await self.get_item_market_data(item)
            market_value = get_market_value(market_data)

            if not market_value:
                pass # TODO handle null cases

            amount = market_value.amount

            return amount * (1 - change) if percentage else amount - change
        
        return await self.change_price(items, new_price, condition)
        
    

    

