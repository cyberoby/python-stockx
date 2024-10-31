import asyncio

from stockx.api import (
    Catalog,
    Orders,
    Listings,
    Batch,
)
from stockx.api.client import StockXAPIClient

from datetime import date, datetime


async def main() -> None:
    client = StockXAPIClient('api.stockx.com', 'v2')
    await client.initialize()
    catalog = Catalog(client)
    orders = Orders(client)
    listings = Listings(client)

    # product = await catalog.get_product('da36823e-0d43-4ca4-a334-ce485c582948')
    # print(product)

    batch = Batch(client)

    print('------------LISTINGS--------------\n')
    async for listing in listings.get_all_listings(
        limit=3,
        from_date=datetime(2021, 1, 1),
        to_date=datetime(2021, 2, 1)
    ):
        print(listing)
        print('\n--------------------------------\n')
        await asyncio.sleep(3)

    print('\n------------ORDERS--------------\n')
    async for order in orders.get_orders_history(
        from_date=datetime(2021, 1, 1),
        to_date=datetime(2021, 2, 1),
        limit=3
    ):
        print(order)
        print('\n--------------------------------\n')
        await asyncio.sleep(1)

    await client.close()


asyncio.run(main())