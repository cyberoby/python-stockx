from ..api import StockX
from ..cache import cache_by
from ..models import Product


__all__ = (
    'product_by_sku',
    'product_by_url',
)


@cache_by('sku')
async def product_by_sku(stockx: StockX, sku: str) -> Product | None:
    """Search a product by SKU.

    Parameters
    ----------
    stockx : `StockX`
        StockX API interface
    sku : `str`
        Product SKU/style ID to search for

    Returns
    -------
    `Product` or `None`
        Product if found, None otherwise

    Notes
    -----
    Since product data rarely changes, results are cached indefinitely.
    """
    async for product in stockx.catalog.search_catalog(
        query=sku,
        page_size=50,
        limit=50
    ):
        if sku in product.style_id:
            return product
    else:
        return None


@cache_by('stockx_url')
async def product_by_url(stockx: StockX, stockx_url: str) -> Product | None:
    """Search a product by StockX URL.

    Parameters
    ----------
    stockx : `StockX`
        StockX API interface
    stockx_url : `str`
        StockX product URL to search for

    Returns
    -------
    `Product` or `None`
        Product if found, None otherwise

    Notes
    -----
    Since product data rarely changes, results are cached indefinitely.
    """
    async for product in stockx.catalog.search_catalog(
        query=stockx_url, 
        page_size=50, 
        limit=50
    ):
        if product.url_key in stockx_url:
            return product
    else:
        return None

