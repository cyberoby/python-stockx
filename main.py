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
    batch = Batch(client)
    

    await client.close()


asyncio.run(main())