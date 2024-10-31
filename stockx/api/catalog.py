from typing import AsyncIterator

from stockx.api.base import StockXAPIBase
from stockx.models.core import (
    Product, 
    Variant, 
    MarketData,
)


class Catalog(StockXAPIBase):
    
    async def get_product(
            self, 
            product_id: str
    ) -> Product:
        response = await self.client.get(f'/catalog/products/{product_id}')
        return Product.from_json(response.data)
    
    async def get_all_product_variants(
            self, 
            product_id: str
    ) -> list[Variant]:
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants'
        )
        return [Variant.from_json(item) for item in response.data]
    
    async def get_product_variant(
            self, 
            product_id: str, 
            variant_id: str
    ) -> Variant:
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants/{variant_id}'
        )
        return Variant.from_json(response.data)
    
    async def get_variant_market_data(
            self, 
            product_id: str, 
            variant_id: str, 
            currency_code: str
    ) -> MarketData:
        params = {'currencyCode': currency_code}    
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants/{variant_id}/market-data',
            params=params
        )
        return MarketData.from_json(response.data)
    
    async def get_product_market_data(
            self, 
            product_id: str, 
            currency_code: str
    ) -> list[MarketData]:
        params = {'currencyCode': currency_code}    
        response = await self.client.get(
            f'/catalog/products/{product_id}/market-data', 
            params=params
        )
        return [MarketData.from_json(item) for item in response.data]
    
    async def search_catalog(
            self, 
            query: str, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[Product]:
        params = {'query': query}
        async for product in self._page(
            endpoint='/catalog/search', 
            results_key='products',
            params=params,
            limit=limit,
            page_size=page_size
        ):
            yield Product.from_json(product)
