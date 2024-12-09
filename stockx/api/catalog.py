from collections.abc import AsyncIterator

from .base import StockXAPIBase
from ..cache import cache_by
from ..models import (
    Currency,
    Product, 
    Variant, 
    MarketData,
)


class Catalog(StockXAPIBase):
    """Interface for interacting with the StockX catalog."""

    @cache_by('product_id')
    async def get_product(
            self, 
            product_id: str
    ) -> Product:
        """Get a product by its ID.

        Notes
        -----
        Results are cached indefinitely.
        """
        response = await self.client.get(f'/catalog/products/{product_id}')
        return Product.from_json(response.data)
    
    @cache_by('product_id')
    async def get_all_product_variants(
            self, 
            product_id: str
    ) -> list[Variant]:
        """Get all variants for a product.

        Notes
        -----
        Results are cached indefinitely.
        """
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants'
        )
        return [Variant.from_json(item) for item in response.data]
    
    @cache_by('product_id', 'variant_id')
    async def get_product_variant(
            self, 
            product_id: str, 
            variant_id: str
    ) -> Variant:
        """Get a variant by its product and variant IDs.

        Notes
        -----
        Results are cached indefinitely.
        """
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants/{variant_id}'
        )
        return Variant.from_json(response.data)
    
    @cache_by('product_id', 'variant_id', 'currency', ttl=30)
    async def get_variant_market_data(
            self, 
            product_id: str, 
            variant_id: str, 
            currency: Currency
    ) -> MarketData:
        """Get market data for a variant.

        Notes
        -----
        Results are cached for 30 seconds.
        """
        params = {'currencyCode': currency.value}    
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants/{variant_id}/market-data',
            params=params
        )
        return MarketData.from_json(response.data)
    
    @cache_by('product_id', 'currency', ttl=30)
    async def get_product_market_data(
            self, 
            product_id: str, 
            currency: Currency
    ) -> list[MarketData]:
        """Get market data for all variants of a product.

        Notes
        -----
        Results are cached for 30 seconds.
        """
        params = {'currencyCode': currency.value}    
        response = await self.client.get(
            f'/catalog/products/{product_id}/market-data', 
            params=params
        )
        return [MarketData.from_json(item) for item in response.data]
    
    async def search_catalog(
            self, 
            query: str, 
            limit: int | None = None, 
            page_size: int = 10
    ) -> AsyncIterator[Product]:
        """Search the catalog for products."""
        params = {'query': query}
        async for product in self._page(
            endpoint='/catalog/search', 
            results_key='products',
            params=params,
            limit=limit,
            page_size=page_size
        ):
            yield Product.from_json(product)
