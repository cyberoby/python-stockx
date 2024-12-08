from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ..api import StockX 
from ..models import Currency, ListingDetail


@asynccontextmanager
async def mock_listing(
        stockx: StockX, 
        amount: float = 1000,
        currency: Currency = Currency.EUR,
) -> AsyncIterator[ListingDetail]:

    product = await anext(stockx.catalog.search_catalog('adidas'))
    variants = await stockx.catalog.get_all_product_variants(product.id)
    create = await stockx.listings.create_listing(
        amount=amount,
        variant_id=variants[0].id,
        currency=currency,
        active=True,
    )
    if not await stockx.listings.operation_succeeded(create):
        pass # raise what?
    
    try:
        listing = await stockx.listings.get_listing(create.listing_id)
        yield listing
    finally:
        delete = await stockx.listings.delete_listing(create.listing_id)
        if not await stockx.listings.operation_succeeded(delete):
            pass # log