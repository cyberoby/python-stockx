from collections.abc import (
    Awaitable,
    Callable,
    Iterable, 
    Iterator,
)
from operator import xor

from .batch.operations import (
    UpdateResult,
    publish_listings,
    update_listings, 
    update_quantity,
)
from .item import Item, ListedItem
from .market import (
    ItemMarketData, 
    MarketValue,
    create_item_market_data, 
)
from .query import create_items_query, ItemsQuery
from ..mock import mock_listing
from ...api import StockX


DynamicPrice = Callable[[ListedItem], float]  
AsyncDynamicPrice = Callable[[ListedItem], Awaitable[float]]  
Price = float

Condition = Callable[[ListedItem], bool]  
AsyncCondition = Callable[[ListedItem], Awaitable[bool]]


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

    def register_price_change(self, item: ListedItem) -> None:
        self._price_updates.add(item)

    def register_quantity_change(self, item: ListedItem) -> None:
        self._quantity_updates.add(item)

    def items(self) -> ItemsQuery:
        return create_items_query(self)

    async def load(self) -> None:
        await self.load_fees()

    async def sell(self, items: Iterable[Item]) -> list[ListedItem]:
        results = await publish_listings(self.stockx, items)
        return [
            ListedItem(
                item=result.item, 
                inventory=self, 
                listing_ids=result.created
            )
            for result in results
        ]

    async def beat_lowest_ask(
            self,
            items: Iterable[ListedItem], 
            market_value: Callable[[ItemMarketData], MarketValue],
            beat_by: Callable[[ListedItem], float] | float = 1, # computed?
            async_beat_by: Callable[[ListedItem], Awaitable[float]] | None = None, 
            percentage: bool = False,
            condition: Callable[[ListedItem], bool] | None = None,
            async_condition: Callable[[ListedItem], Awaitable[bool]] | None = None,
    ):
        if beat_by != 1 and async_beat_by:
            raise ValueError("Provide either 'beat_by' or 'async_beat_by', not both.")
        
        async def new_price(item):
            if beat_by
            market_data = await self.get_item_market_data(item)
            lowest_ask = market_data.lowest_ask.amount
            if percentage:
                change = change * lowest_ask
        
    
    async def change_price(
            self,
            items: Iterable[Item],
            new_price: DynamicPrice | AsyncDynamicPrice | Price,
            condition: Condition | AsyncCondition | None = None,
    ):
        async def check(item):
            if not condition:
                return True
            try:
                return await condition(item)
            except TypeError:
                return condition(item)
            
        items_to_update = [item for item in items if await check(item)]

        for item in items_to_update:
            if not callable(new_price):
                item.price = new_price
                continue
            try:
                item.price = await new_price(item)
            except TypeError:
                item.price = new_price(item)

        
        await update_listings(self.stockx, items_to_update)
    
        self._price_updates.difference_update(items_to_update)


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
    
    async def get_item_market_data(
            self, 
            item: Item | ListedItem
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
        
        return create_item_market_data(variant_market_data, self)
    
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
        
    

    

