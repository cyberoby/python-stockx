from collections.abc import Iterable
from dataclasses import dataclass
from itertools import groupby, batched
from functools import reduce
from operator import attrgetter
from typing import Generator, TypeVar

from stockx.api.client import StockXAPIClient
from stockx.api import (
    Batch,
    Catalog,
    Listings,
    Orders
)
from stockx.models import (
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
    
    
@dataclass
class ItemMarketData:
    lowest_ask: float
    highest_bid: float
    earn_more: float
    flex_lowest_ask: float

    
@dataclass
class InventoryItem:
    variant_id: str
    product_id: str
    price: float
    quantity: int # computed
    skus: tuple[str, ...] | None = None
    size: str | None = None
    payout: float | None = None # computed
    market_data: ItemMarketData | None = None


def group_and_sum(
        iterable: Iterable[T], 
        /, 
        *, 
        group_keys: Iterable[str], 
        sum_attr: str
) -> Generator[T, None, None]:
    
    def reduce_func(accumulated, item):
        item_attr = getattr(item, sum_attr)
        accumulated_attr = getattr(accumulated, sum_attr)
        setattr(item, sum_attr, accumulated_attr + item_attr)
        return item
    
    groups = groupby(iterable, key=attrgetter(*group_keys))
    for _, group in groups:
        yield reduce(reduce_func, group)


async def create_listings(items: Iterable[InventoryItem]) -> None:
    grouped_items = group_and_sum(
        items, 
        group_keys=('variant_id', 'price'), 
        sum_attr='quantity',
    )
    for b in batched(grouped_items, 500):
        await batch.create_listings(
            BatchInputCreate(item.variant_id, item.price, item.quantity) 
            for item 
            in b
        )


items = [
    InventoryItem(variant_id='id', product_id='pid', price=100, quantity=1),
    InventoryItem(variant_id='id', product_id='pid', price=100, quantity=3),
    InventoryItem(variant_id='id2', product_id='pid', price=120, quantity=10),
    InventoryItem(variant_id='id2', product_id='pid', price=120, quantity=2),
]



grouped_items = group_and_sum(items, group_keys=('variant_id', 'price'), sum_attr='quantity')

for g in grouped_items:
    print(g)
