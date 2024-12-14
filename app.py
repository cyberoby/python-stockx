import asyncio
import os

from dotenv import load_dotenv

import stockx
from stockx import StockX, StockXAPIClient


ACCOUNT_TYPE = 'PRIVATE'


load_dotenv()

x_api_key = os.getenv('X_API_KEY')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv(f'REFRESH_TOKEN_{ACCOUNT_TYPE}')


async def main() -> None:   
    client = StockXAPIClient(
        hostname='api.stockx.com', 
        version='v2', 
        x_api_key=x_api_key,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )

    async with StockX(client=client) as sx:
        try:
            birkenstock = 'a39a5ae3-be6e-461d-99e0-96441488818f'
            async for listing in sx.listings.get_all_listings(
                limit=1, 
                page_size=100
            ):
                async for operation in sx.listings.get_all_listing_operations(
                    listing.id, 
                    limit=1, 
                    page_size=100
                ):
                    print(operation.changes)
                    print('\n---------\n')
        except Exception as e:
            print(f'{e=}')



if __name__ == '__main__':
    asyncio.run(main())