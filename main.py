import asyncio

from stockx.api import (
    Catalog,
    Orders,
    Listings,
    Batch,
)
from stockx.api.client import StockXAPIClient

import json

from datetime import date, datetime


async def main() -> None:
    client = StockXAPIClient('api.stockx.com', 'v2')
    await client.initialize()
    catalog = Catalog(client)
    orders = Orders(client)
    listings = Listings(client)

    product = await catalog.get_product('da36823e-0d43-4ca4-a334-ce485c582948')
    print(product)

    # print('------------LISTINGS--------------\n')
    async for listing in listings.get_all_listings(
        limit=1
    ):
        print(listing)
        # print('\n--------------------------------\n')
        await asyncio.sleep(3)


    await client.close()


asyncio.run(main())