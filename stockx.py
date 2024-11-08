from __future__ import annotations

from collections.abc import Iterable, Iterator, AsyncIterator, AsyncIterable
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from itertools import groupby, batched, chain
from functools import reduce, singledispatch
from operator import attrgetter
from typing import TypeVar
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


async def batch_completed(batch_ids: Iterable[str], max_wait_time: int):
    for batch_id in batch_ids:
        sleep, waited = 1, 0
        while waited <= max_wait_time:
            await asyncio.sleep(sleep)

            status = await batch.get_create_listings_status(batch_id)
            if status.item_statuses.queued == 0:
                break
            
            waited += sleep
            sleep = min(sleep * 2, max_wait_time - waited)
        else:
            raise BatchTimeOutError
        
        
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
            stockx: StockXAPIClient, 
            currency = 'EUR', 
            minimum_transaction_fee = 5,
            shipping_fee = 7,
    ):
        # later consolidate in one stockx object (with search product sku bla bla)
        self.batch = Batch(stockx)          
        self.catalog = Catalog(stockx)
        self.listings = Listings(stockx)    
        self.orders = Orders(stockx)

        self.currency = currency

        self.transaction_fee = 0 # load 
        self.payment_fee = 0 # load
        self.shipping_fee = shipping_fee
        self.minimum_transaction_fee = minimum_transaction_fee

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
        '__quantity'
        '__skus', 
        '__size',
    )

    def __init__(
            self,
            *,
            variant_id: str,
            price: float,
            quantity: int,
    ) -> None:
        self.variant_id = variant_id
        self.price = price
        self._quantity = quantity

        self._sku = ''
        self._size = ''
        self.__payout = None # compute fees upon inventory load
        self.__market_data = None # mmmhh fetch when how?

        self._product_id = ''  # init?
        self._inventory: Inventory = None

    @classmethod
    async def from_listings(
        cls, 
        listings: AsyncIterable[Listing]
    ) -> list[InventoryItem]:
        items: dict[str, dict[float, InventoryItem]] = {}
        async for listing in listings:
            amounts_dict = items.setdefault(listing.variant_id, {})
            if listing.amount in amounts_dict:
                items[listing.variant_id][listing.amount].quantity += 1
            else:
                item = InventoryItem(
                    variant_id=listing.variant_id,
                    price=listing.amount,
                    quantity=1
                )
                item._product_id = listing.product.id
                item._sku = listing.sku
                item._size = listing.size
                items[listing.variant_id, listing.amount] = item

        return []
            

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}'
            + f'({self.variant_id=}, {self.price=}, {self.quantity=})'
        ).replace('self.', '')
    
    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if int(value) < 0:
            raise ValueError("Quantity can't be negative.")
        self._quantity = int(value)

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
        await batch_completed(batch_ids, 60)
    except BatchTimeOutError:
        pass # TODO: partial report
    
    results = []
    for batch_id in batch_ids:
        results += await batch.get_create_listings_items(
            batch_id, 
            status='COMPLETED'
        )
    
    return CreatedItem.from_batch_results(results)
    
ANY = None

class ListedItems:

    def __init__(self):
        self._filters = defaultdict(set)
        self._sku_sizes = defaultdict(set)
    
    async def all(self):
        async for listing in self._listings():
            yield listing

    async def first(self):
        async for listing in self._listings():
            return listing
        return None
    
    async def limit(self, n: int):
        i = 0
        async for listing in self._listings():
            yield listing
            i += 1
            if i > n:
                break
    
    async def offset(self, n: int):
        i = 0
        async for listing in self._listings():
            i += 1
            if i > n:
                yield listing

    async def exists(self) -> bool:
        async for _ in self._listings():
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
            add_to('skus' if sku else 'sizes', [sku] or sizes)

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


def get_listed_items():
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


