from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ..api import StockX 
from ..logging import logger
from ..models import Currency, ListingDetail


@asynccontextmanager
async def mock_listing(
        stockx: StockX, 
        amount: float = 1000,
        currency: Currency = Currency.EUR,
) -> AsyncIterator[ListingDetail]:
    """Create a temporary test listing that gets cleaned up after use.

    Parameters
    ----------
    stockx : `StockX`
        The StockX API interface to use.
    amount : `float`, default 1000
        The price of the listing. Set a high price to avoid being sold.
    currency : `Currency`, default `Currency.EUR`
        The currency for the listing amount.

    Yields
    ------
    `ListingDetail`
        The temporary listing.

    Raises
    ------
    `RuntimeError`
        If the listing creation fails.

    Examples
    --------
    >>> async with mock_listing(stockx) as listing:
    ...     # Check if there's a discount on selling fees 
    ...     if listing.payout.transaction_fee < 0.05:
    ...         print(f'Discount on selling fees!')
    """
    product = await anext(stockx.catalog.search_catalog('adidas'))
    variants = await stockx.catalog.get_all_product_variants(product.id)
    create = await stockx.listings.create_listing(
        amount=amount,
        variant_id=variants[0].id,
        currency=currency,
        active=True,
    )
    if not await stockx.listings.operation_succeeded(create):
        message = create.error if create.error else 'Unknown error'
        raise RuntimeError(f'Failed to create mock listing: {message}')
    
    try:
        listing = await stockx.listings.get_listing(create.listing_id)
        yield listing
    finally:
        delete = await stockx.listings.delete_listing(create.listing_id)
        if not await stockx.listings.operation_succeeded(delete):
            logger.warning(
                f'Failed to delete mock listing {create.listing_id}: '
                f'{delete.error}'
            )