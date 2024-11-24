import asyncio
import os
from dotenv import load_dotenv

from stockx import StockX, StockXAPIClient
from stockx.ext import search
from stockx.ext.inventory import Item


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
    
    async with StockX(client) as stockx:
        # product = await search.product_by_sku(stockx, 'L41619900')
        # print(product)

        last_order = [order async for order in stockx.orders.get_orders_history(limit=1)][0]
        last_order_detail = await stockx.orders.get_order(last_order.number)

        print(last_order_detail)


if __name__ == '__main__':
    asyncio.run(main())