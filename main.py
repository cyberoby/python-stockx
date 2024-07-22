import asyncio
from stockx.api.client import StockXAPIClient
from stockx.api.catalog import Catalog
from stockx.api.orders import Orders

import json

from datetime import date, datetime


async def main() -> None:
    client = StockXAPIClient('api.stockx.com', 'v2')
    await client.initialize()
    catalog = Catalog(client)
    orders = Orders(client)

    # product = await catalog.get_product('da36823e-0d43-4ca4-a334-ce485c582948')
    # print(product)

    print('------------ORDERS--------------\n')
    async for order in orders.get_orders_history(
        from_date=datetime.fromisoformat('2024-01-01'), 
        limit=2
    ):
        print(order)
        print('\n--------------------------------\n')
        await asyncio.sleep(3)


    await client.close()


asyncio.run(main())