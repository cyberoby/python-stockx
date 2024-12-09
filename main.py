import asyncio
import os
from dotenv import load_dotenv

from stockx import StockX, StockXAPIClient
from stockx.ext import search, mock_listing
from stockx.ext.inventory import Inventory
from stockx.cache import cache_by

HOSTNAME = 'api.stockx.com'
VERSION = 'v2'

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
X_API_KEY = os.getenv('X_API_KEY')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')

async def main():

    client = StockXAPIClient(
        hostname=HOSTNAME, 
        version=VERSION, 
        x_api_key=X_API_KEY, 
        client_id=CLIENT_ID, 
        client_secret=CLIENT_SECRET, 
        refresh_token=REFRESH_TOKEN
    )
    from stockx.models import OrderStatusClosed
    from datetime import datetime
    async with StockX(client) as stockx:
        async for order in stockx.orders.get_orders_history(
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 1),
            order_status=OrderStatusClosed.DIDNOTSHIP,
            limit=1,
            page_size=50
        ):
            print(f'Order Number: {order.number} (Type: {type(order.number).__name__})')
            print(f'Status: {order.status} (Type: {type(order.status).__name__})')
            print(f'Created At: {order.created_at} (Type: {type(order.created_at).__name__})')



    #     async with Inventory(stockx) as inventory:
    #         items = await (
    #             inventory.items().
    #             filter(lambda item: 'DA8857-001' in item.style_id)
    #             .all()
    #         )
    #         item = items[0]
    #         print(item.style_id)
    #         print(item.name)
    #         print(item.size)
# 
# 
    #     batch_id = 'af6747c1-60ed-4074-a3c6-7b4a17411229'
    #     status = await stockx.batch.delete_listings_status(batch_id)
    #     items = await stockx.batch.delete_listings_items(batch_id)
    #     print(status)
    #     print('-------')
    #     for item in items:
    #         print(item)

    



if __name__ == '__main__':
    asyncio.run(main())