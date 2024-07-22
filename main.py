import asyncio
from stockx.api.client import StockXAPIClient
from stockx.api.catalog import Catalog


async def main() -> None:
    client = StockXAPIClient('api.stockx.com', 'v2')
    await client.initialize()
    catalog = Catalog(client)


    p = await catalog.get_product('da36823e-0d43-4ca4-a334-ce485c582948')
    async for product in catalog.search_catalog('black white', limit=10):
        print(product.style_id)
        print('---------------------------------')
    
    await client.close()

asyncio.run(main())