from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from collections import Counter
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

    
@dataclass
class InventoryItem:
    variant_id: str
    product_id: str # might not be needed
    price: float
    quantity: int # computed
    skus: tuple[str, ...] | None = None
    size: str | None = None
    payout: float | None = None # computed
    market_data: ItemMarketData | None = None


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

class ListedItems:

    async def all(self):
        async for listing in listings.get_all_listings(
            listing_statuses=['ACTIVE'], 
            limit=5, 
            page_size=100
        ):
            yield listing

    async def filter(
            self, 
            variant_ids: Iterable[str] | None = None,
            skus: Iterable[str] | None = None,
            sku_sizes: Mapping[str, Iterable[str]] | None = None
    ): 
        variant_ids = list(variant_ids)

        for sku in skus:
            product = await search_product_by_sku(sku)
            if not product:
                continue # raise exception?
            variants = await catalog.get_all_product_variants(product.product_id)
            variant_ids.extend(variant.variant_id for variant in variants)

        for sku, sizes in sku_sizes.items():
            if sku in skus:
                continue
            product = await search_product_by_sku(sku)
            if not product:
                continue # raise exception?
            variants = await catalog.get_all_product_variants(product.product_id)
            variant_ids.extend(
                variant.variant_id for variant in variants
                if variant.variant_value in sizes
            )



def get_listed_items():
    return ListedItems()


async def main():

    # items = [
    #     InventoryItem(variant_id='id', product_id='pid', price=100, quantity=1),
    #     InventoryItem(variant_id='id', product_id='pid', price=100, quantity=3),
    #     InventoryItem(variant_id='id2', product_id='pid', price=120, quantity=10),
    #     InventoryItem(variant_id='id2', product_id='pid', price=120, quantity=2),
    # ]

    await client.initialize()

    async for item in get_listed_items().all():
        print(item)

    await client.close()
    # grouped_items = group_and_sum(items, group_keys=('variant_id', 'price'), sum_attr='quantity')
    # 
    # for g in grouped_items:
    #     print(g)


if __name__ == '__main__':
    asyncio.run(main())


