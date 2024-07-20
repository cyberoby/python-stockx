import asyncio
from typing import AsyncIterator

from models import (
    StockXBaseModel,
    Product, 
    Variant, 
    MarketData
)

from client import StockXAPIClient


class StockXAPI:

    def __init__(self, client: StockXAPIClient) -> None:
        self.client = client

    async def initialize(self) -> None:
        await self.client.initialize()
    
    async def close(self) -> None:
        await self.client.close()

    async def get_product(
            self, product_id: str
        ) -> Product:
        response = await self.client.get(
            f'/catalog/products/{product_id}'
        )
        return Product.from_json(response.data)
    
    async def get_all_product_variants(
            self, product_id: str
    ) -> list[Variant]:
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants'
        )
        return [Variant.from_json(item) for item in response.data]
    
    async def get_product_variant(
            self, product_id: str, variant_id: str
    ) -> Variant:
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants/{variant_id}'
        )
        return Variant.from_json(response.data)
    
    async def get_variant_market_data(
            self, product_id: str, variant_id: str, currency_code: str
    ) -> MarketData:
        params = {'currencyCode': currency_code}    
        response = await self.client.get(
            f'/catalog/products/{product_id}/variants/{variant_id}/market-data', 
            params=params
        )
        return MarketData.from_json(response)
    
    async def search_catalog(
            self, query: str, limit: int = None, page_size: int = 10
    ) -> AsyncIterator[Product]:
        params = {
            'query': query
        }
        async for product in self._page(
            endpoint='/catalog/search', 
            results_key='products',
            params=params,
            limit=limit,
            page_size=page_size
        ):
            yield Product.from_json(product)
     
    async def _page(
            self, 
            endpoint: str,
            results_key: str,
            params: dict = None, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[dict]:
        params = params if params is not None else {}
        current_page = 1
        count = 0
        check = lambda count, max: count < max if max is not None else True

        while check(count, limit):
            params['pageNumber'] = current_page
            params['pageSize'] = page_size

            response = await self.client.get(endpoint, params=params)

            current_page = int(response.data.get('pageNumber'))
            has_next_page = bool(response.data.get('hasNextPage', False))
            results = response.data.get(results_key, [])

            for item in results:
                yield item
                count += 1
                await asyncio.sleep(5)
                if not check(count, limit):
                    break

            if not has_next_page: 
                break


async def main() -> None:
    client = StockXAPIClient('api.stockx.com', 'v2')
    stockx = StockXAPI(client)
    await stockx.initialize()

    p = await stockx.get_product('da36823e-0d43-4ca4-a334-ce485c582948')
    async for product in stockx.search_catalog('black white', limit=10):
        print(product.style_id)
        print('---------------------------------')
    
    await stockx.close()


asyncio.run(main())