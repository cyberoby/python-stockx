import asyncio
import os
from dotenv import load_dotenv

from stockx import StockX, StockXAPIClient
from stockx.ext import search, mock_listing
from stockx.ext.inventory import Inventory


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
        # async with Inventory(stockx) as inventory:
        #     items = await inventory.items().filter_by(style_ids=['DN1266-010']).all()
        #     item = items[0]
        #     print(item.style_id)
        #     print(item.name)
        #     print(item.size)


        batch_id = '94d49028-ce3d-4b72-9cac-68bd0681a178'
        # status = await stockx.batch.update_listings_status(batch_id)
        # items = await stockx.batch.update_listings_items(batch_id)
        # print(status)
        # print('-------')
        # for item in items:
        #     print(item)
        await stockx.batch.update_listings_completed([batch_id], 10)
        

if __name__ == '__main__':
    asyncio.run(main())