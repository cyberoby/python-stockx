from __future__ import annotations

from collections.abc import Iterable, Iterator, AsyncIterator, AsyncIterable, Callable
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from itertools import groupby, batched, chain
from functools import reduce, singledispatch
from operator import attrgetter
from typing import TypeVar, Any
import asyncio

from stockx.api.client import StockXAPIClient
from stockx.api import (
    Batch,
    Catalog,
    Listings,
    Orders
)
from stockx.exceptions import BatchTimeOutError
from stockx.models import (
    BatchCreateResult,
    BatchInputCreate,
    Product,
    Variant,
    Listing,
)

T = TypeVar('T')

client = StockXAPIClient('api.stockx.com', 'v2')
batch = Batch(client)
catalog = Catalog(client)
listings = Listings(client)
orders = Orders(client)


async def search_product_by_sku(sku: str) -> Product | None:
    async for product in catalog.search_catalog(query=sku):
        if sku in product.style_id:
            return product
    else:
        return None
    

async def search_product_by_url(stock_url: str) -> Product | None:
    async for product in catalog.search_catalog(query=stock_url):
        if product.url_key in stock_url:
            return product
    else:
        return None


async def batch_completed(batch_ids, get_batch_status_coro, timeout):
    completed_batch_ids = set()
    pending_batch_ids = set(batch_ids)

    sleep, waited = 1, 0
    while waited <= timeout:
        await asyncio.sleep(sleep)

        for batch_id in pending_batch_ids:
            status = await get_batch_status_coro(batch_id)
            if status.item_statuses.queued == 0:
                completed_batch_ids.update(batch_id)

        pending_batch_ids.difference_update(completed_batch_ids)
        if len(pending_batch_ids) == 0:
            return
        
        waited += sleep
        sleep = min(sleep * 2, timeout - waited)
    else:
        raise BatchTimeOutError # TODO: add report on completed items??
    

def batch_create_completed(batch_ids: Iterable[str], timeout: int):
    return batch_completed(batch_ids, batch.get_create_listings_status, timeout)


def batch_delete_completed(batch_ids: Iterable[str], timeout: int):
    return batch_completed(batch_ids, batch.get_delete_listings_status, timeout)


def batch_update_completed(batch_ids: Iterable[str], timeout: int):
    return batch_completed(batch_ids, batch.get_update_listings_status, timeout)
        
        
def group_and_sum(
        iterable: Iterable[T], 
        /, 
        *, 
        group_keys: Iterable[str], 
        sum_attr: str
) -> Iterator[T]:
    
    def reduce_func(accumulated, item):
        item_attr = getattr(item, sum_attr)
        accumulated_attr = getattr(accumulated, sum_attr)
        setattr(item, sum_attr, accumulated_attr + item_attr)
        return item
    
    groups = groupby(iterable, key=attrgetter(*group_keys))
    for _, group in groups:
        yield reduce(reduce_func, group)


@dataclass(slots=True)
class ErrorDetail:
    message: str
    occurrences: int

    @classmethod
    def from_counter(cls, errors: Counter) -> Iterator[ErrorDetail]:
        for message, occurrences in errors.items():
            yield cls(message, occurrences)


@dataclass(slots=True)
class CreatedItem:
    variant_id: str
    price: float
    listings_ids: list[str] = field(default_factory=list)
    errors_detail: list[ErrorDetail] = field(default_factory=list)

    @property
    def quantity(self) -> int:
        return len(self.listings_ids)

    @property
    def errors(self) -> int:
        return sum(error.occurrences for error in self.errors_detail)
    
    @classmethod
    def from_batch_results(
            cls, 
            results: Iterable[BatchCreateResult]
    ) -> Iterator[CreatedItem]:
        
        # group by variant_id, price, and error
        def key(result: BatchCreateResult) -> tuple[str, float, str]:
            return (
                result.listing_input.variant_id, 
                result.listing_input.amount,
                bool(result.error)
            )
        
        for (variant_id, price, failed), results_group in groupby(results, key=key):
            if failed:
                errors = Counter(res.error for res in results_group)
                errors_detail = list(ErrorDetail.from_counter(errors))
            else:
                listing_ids = [res.result.listing_id for res in results_group]
            
            yield cls(variant_id, price, listing_ids, errors_detail)


@dataclass
class ItemMarketData:
    lowest_ask: float
    highest_bid: float
    earn_more: float
    flex_lowest_ask: float


class Inventory:

    def __init__(
            self, 
            client: StockXAPIClient, 
            currency = 'EUR', 
            minimum_transaction_fee = 5,
            shipping_fee = 7,
    ):
        # later consolidate in one stockx object (with search product sku bla bla)
        self.batch = Batch(client)          
        self.catalog = Catalog(client)
        self.listings = Listings(client)    
        self.orders = Orders(client)

        self.currency = currency

        self.transaction_fee = 0 # load 
        self.payment_fee = 0 # load
        self.shipping_fee = shipping_fee
        self.minimum_transaction_fee = minimum_transaction_fee

        self._price_updates: set[InventoryItem] = set()
        self._quantity_updates: set[InventoryItem] = set()

    def register_price_change(self, item: InventoryItem) -> None:
        self._price_updates.add(item)

    def register_quantity_change(self, item: InventoryItem) -> None:
        self._quantity_updates.add(item)

    async def load(self) -> None:
        await self.load_fees()

    async def load_fees(self) -> None:
        async for listing in self.listings.get_all_listings(
            listing_statuses='ACTIVE',
            limit=100,
            page_size=100,
        ):
            detail = await self.listings.get_listing(listing.id)
            if detail.payout:
                self.transaction_fee = detail.payout.transaction_fee
                self.payment_fee = detail.payout.payment_fee
                return
        
        async with mock_listing(self) as detail:
            if detail and detail.payout:
                self.transaction_fee = detail.payout.transaction_fee
                self.payment_fee = detail.payout.payment_fee
                return
        
        raise RuntimeError('Unable to load fees.')
    
    async def update(self) -> None:
        listings_to_delete = set()
        listings_to_create = set()

        for item in self._quantity_updates:
            quantity_change = item.quantity - len(item.listing_ids)

            if quantity_change < 0:
                listings_to_delete.update(item.listing_ids[quantity_change:])
                item.listing_ids = item.listing_ids[:-quantity_change]

            if quantity_change > 0:
                listings_to_create.update(item)

        listings_to_update = self._price_updates
        
        

            
@asynccontextmanager
async def mock_listing(inventory: Inventory, amount: float = 1000): # TODO: change inventory with stockx
    product = await anext(inventory.catalog.search_catalog('adidas'))
    variants = await inventory.catalog.get_all_product_variants(product.id)
    create = await inventory.listings.create_listing(
        amount=amount,
        variant_id=variants[0].id,
        currency_code=inventory.currency,
    )
    if not await inventory.listings.operation_succeeded(create):
        pass # raise what?
    
    try:
        listing = await inventory.listings.get_listing(create.listing_id)
        yield listing
    finally:
        delete = await inventory.listings.delete_listing(create.listing_id)
        if not await inventory.listings.operation_succeeded(delete):
            pass # log

    
class InventoryItem:
    
    __slots__ = (
        'variant_id', 
        'price', 
        '_quantity'
        '_sku', 
        '_size',
    )

    def __init__(
            self,
            *,
            variant_id: str,
            price: float,
            quantity: int,
    ) -> None:
        self.variant_id = variant_id
        self._price = price
        self._quantity = quantity

        self._sku = ''
        self._size = ''
        self.__payout = None # compute fees upon inventory load
        self.__market_data = None # mmmhh fetch when how?

        self._product_id = ''  # init?
        self._inventory: Inventory = None
        self.listing_ids: list[str] = []

    @classmethod
    async def from_listings(
            cls, 
            listings: AsyncIterable[Listing]
    ) -> list[InventoryItem]:
        items: dict[str, dict[float, InventoryItem]] = {}

        async for listing in listings:
            amounts_dict = items.setdefault(listing.variant_id, {})
            
            if listing.amount in amounts_dict:
                amounts_dict[listing.amount].quantity += 1
                amounts_dict[listing.amount].listing_ids.append(listing.id)
            else:
                item = InventoryItem(
                    variant_id=listing.variant_id,
                    price=listing.amount,
                    quantity=1
                )
                item.listing_ids.append(listing.id)
                item._product_id = listing.product.id
                item._sku = listing.sku
                item._size = listing.size
                amounts_dict[listing.amount] = item

        return [
            inventory_item 
            for amount in items.values() 
            for inventory_item in amount.values()
        ]

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}'
            + f'({self.variant_id=}, {self._price=}, {self.quantity=})'
        ).replace('self.', '')
    
    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if value < 0:
            raise ValueError("Quantity can't be negative.")
        if int(value) != self._quantity:
            self._quantity = int(value)
            if self._inventory:
                self._inventory.register_quantity_change(self)

    @property
    def price(self) -> float:
        return self._price
    
    @price.setter
    def price(self, value: float) -> None:
        if value != self._price:
            self._price = value
            if self._inventory:
                self._inventory.register_price_change(self)

    @property
    def skus(self) -> tuple[str, ...]:
        if not self._sku:
            raise AttributeError('') # what?
        return self._sku
    
    @property
    def size(self) -> tuple[str, ...]:
        if not self._size:
            raise AttributeError('') # what?
        return self._size
    

async def delete_listings(
        listing_ids: Iterable[str]
) -> list[str]:
    
    batch_ids = []
    for listing_batch in batched(listing_ids, 500):
        batch_status = await batch.delete_listings(listing_batch)
        batch_ids.append(batch_status.batch_id)

    try:
        await batch_delete_completed(batch_ids, 60)
    except BatchTimeOutError:
        pass

    return [
        result.listing_input.id
        for batch_id in batch_ids
        for result
        in await batch.get_delete_listings_items(batch_id, status='COMPLETED')
    ]
    

async def create_listings(
        items: Iterable[InventoryItem]
) -> Iterator[CreatedItem]:
    grouped_items = group_and_sum(
        items, 
        group_keys=('variant_id', 'price'), 
        sum_attr='quantity',
    )

    batch_ids = [] # batch ids to poll

    # perform batch api calls (max 500 items per call)
    for item_batch in batched(grouped_items, 500):
        batch_status = await batch.create_listings(
            BatchInputCreate.from_inventory_items(item_batch)
        )
        batch_ids.append(batch_status.batch_id)

    try:
        await batch_create_completed(batch_ids, 60)
    except BatchTimeOutError:
        pass # TODO: partial report
    
    results = []
    for batch_id in batch_ids:
        results += await batch.get_create_listings_items(
            batch_id, 
            status='COMPLETED'
        )
    
    return CreatedItem.from_batch_results(results)

async def update_listings(
        items: Iterable[InventoryItem]
)
    
ANY = None

class ListedItems:

    __slots__ = ('_filters', '_sku_sizes', '_conditions')

    def __init__(self) -> None:
        self._filters = defaultdict(set)
        self._sku_sizes = defaultdict(set)
        self._conditions = list()
    
    async def all(self) -> list[InventoryItem]:
        return [
            item for item
            in await InventoryItem.from_listings(self._listings())
            if all(condition(item) for condition in self._conditions)
        ]

    async def first(self) -> InventoryItem | None:
        for item in await self.all():
            return item
        return None
    
    async def limit(self, n: int, /) -> list[InventoryItem]:
        return (await self.all())[:n]
    
    async def offset(self, n: int, /) -> list[InventoryItem]:
        return (await self.all())[n:]

    async def exists(self) -> bool:
        for _ in await self.all():
            return True
        return False

    def include(
            self,
            *,
            variant_ids: Iterable[str] = ANY,
            skus: Iterable[str] = ANY,
            sku: str = ANY,
            sizes: Iterable[str] = ANY,
    ) -> ListedItems:
        
        def add_to(key, values):
            if values:
                self._filters[key].update(values)

        add_to('variant_ids', variant_ids)
        add_to('skus', skus)
        
        if bool(sku) ^ bool(sizes):
            add_to('skus' if sku else 'sizes', [sku] if sku else sizes)

        elif sku and sizes:
            self._sku_sizes[sku].update(sizes)

        return self

    def filter_by(
            self,
            *,
            variant_ids: Iterable[str] = ANY,
            skus: Iterable[str] = ANY,
            sku: str = ANY,
            sizes: Iterable[str] = ANY,
    ) -> ListedItems:
        skus = [sku] if sku else skus

        def apply_filter(key, values):
            if not values:
                return
            if _filter := self._filters[key]: 
                _filter.intersection_update(values)
            else:
                _filter.update(values)

        apply_filter('variant_ids', variant_ids)
        apply_filter('skus', skus)
        apply_filter('sizes', sizes)

        if sizes:
            self._sku_sizes = {
                sku: sizelist.intersection(sizes) for sku, sizelist
                in self._sku_sizes.items() if sku in skus
            }
        else:
            self._sku_sizes = {
                sku: sizelist for sku, sizelist 
                in self._sku_sizes.items() if sku in skus
            }

        return self

    def filter(
            self, 
            condition: Callable[[InventoryItem], bool]
    ) -> ListedItems:
        self._conditions.append(condition)
        return self
    
    def _listings(self) -> AsyncIterator[Listing]:
        
        # filter by variant_id if no other filters are applied
        # otherwise retrieve all
        variant_ids = None
        filtered = self._filtered
        if not(self._sku_sizes) and all(
            not(filters)
            for field, filters in self._filters.items() 
            if field != 'variant_ids'
        ):
            variant_ids = self._filters['variant_ids']  
            filtered = lambda x: x

        return filtered(
            listings.get_all_listings(
                variant_ids=variant_ids,
                listing_statuses=['ACTIVE'], 
                # limit=limit, 
                page_size=100,
            )
        )
    
    def _filtered(
            self, 
            listings: AsyncIterable[Listing],
            /,
    ) -> AsyncIterator[Listing]:
        variant_ids = self._filters['variant_ids']
        skus = self._filters['skus']
        sizes = self._filters['sizes']
        
        def sku_size_check(listing: Listing) -> bool:
            return (
                (listing.size in sizes or not sizes)
                and (listing.sku in skus or not skus)
                or  (listing.size in self._sku_sizes[listing.sku])
            )
        
        def check(listing: Listing) -> bool:
            return (listing.variant_id in variant_ids or not variant_ids)
        
        return (
            listing async for listing in listings
            if check(listing) and sku_size_check(listing)
        )


def get_items():
    return ListedItems()


async def main():
    items = [
        InventoryItem(variant_id='id', price=100, quantity=1),
        InventoryItem(variant_id='id', price=100, quantity=3),
        InventoryItem(variant_id='id2', price=120, quantity=10),
        InventoryItem(variant_id='id2', price=120, quantity=2),
    ]

    # await client.initialize()
    # await client.close()

    grouped_items = group_and_sum(items, group_keys=('variant_id', 'price'), sum_attr='quantity')
    
    for g in grouped_items:
        print(g)


if __name__ == '__main__':
    asyncio.run(main())


