import asyncio
import os
from dotenv import load_dotenv

from stockx import StockX, StockXAPIClient
from stockx.ext import search
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
    
    async with (
        StockX(client) as stockx,
        Inventory(stockx) as inventory
    ):
        items = await inventory.items().filter(lambda item: item.payout() > 150).all()
        for item in items:
            print(item)


if __name__ == '__main__':
    asyncio.run(main())