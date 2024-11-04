from collections import defaultdict
from stockx.api import Catalog, Batch, Listings, Orders
from stockx.api.client import StockXAPIClient
import asyncio
import pprint
from datetime import datetime

async def main():

    client = StockXAPIClient('api.stockx.com', 'v2')
    await client.initialize()

    batch = Batch(client)
    catalog = Catalog(client)
    listings = Listings(client)
    orders = Orders(client)

    async for listing in listings.get_all_listings(
        listing_statuses=['ACTIVE'],
        limit=10,
        page_size=12,
        reverse=True,
    ):
        print(listing.created_at.isoformat(timespec='seconds'))
        print('-----------')

    await client.close()


if __name__ == '__main__':
    asyncio.run(main())