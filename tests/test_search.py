import pytest

import stockx
from stockx.ext import search


@pytest.mark.asyncio
async def test_search_product_by_sku(mock_stockx):
    sku = '1203A342-500'
    product = await search.product_by_sku(mock_stockx, sku)
    assert sku in product.style_id
    assert isinstance(product, stockx.Product)

    cached_product = await search.product_by_sku(mock_stockx, sku)
    assert cached_product is product


@pytest.mark.asyncio
async def test_search_product_by_url(mock_stockx):
    url = 'adidas-yeezy-foam-rnnr-onyx'
    product = await search.product_by_url(mock_stockx, url)
    assert url in product.url_key
    assert isinstance(product, stockx.Product)

    cached_product = await search.product_by_url(mock_stockx, url)
    assert cached_product is product


@pytest.mark.asyncio
async def test_search_product_by_sku_not_found(mock_stockx):
    product = await search.product_by_sku(mock_stockx, 'NONEXISTENT-SKU')
    assert product is None


@pytest.mark.asyncio
async def test_search_product_by_url_not_found(mock_stockx):
    product = await search.product_by_url(mock_stockx, 'nonexistent-url')
    assert product is None


