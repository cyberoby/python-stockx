from collections import defaultdict
from stockx.api import Catalog, Batch, Listings, Orders
from stockx.api.client import StockXAPIClient
import asyncio
from datetime import datetime

async def main():

    client = StockXAPIClient('api.stockx.com', 'v2')
    await client.initialize()

    batch = Batch(client)
    catalog = Catalog(client)
    listings = Listings(client)
    orders = Orders(client)

    product = await anext(catalog.search_catalog('adidas'), None)
    if not product:
        pass # custom exception
    
    # 62bed8cb-a31f-4d9b-9f8d-2fd564a0fc37
    variants = await catalog.get_all_product_variants(product.id)
    operation = await listings.create_listing(
        amount=1000,
        variant_id=variants[0].id,
        currency_code='EUR',
        active=True
    )

    while operation.status == 'PENDING':
        operation = await listings.get_listing_operation(
            listing_id=operation.listing_id,
            operation_id=operation.id
        )
    
    if operation.status == 'FAILED':
        pass # custom exception
    
    listing = await listings.get_listing(operation.listing_id)
    
    operation = await listings.delete_listing(listing.id)


    await client.close()


if __name__ == '__main__':
    asyncio.run(main())