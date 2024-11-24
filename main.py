import asyncio

from stockx import StockX
from stockx.ext import search
from stockx.ext.inventory import Item

async def main():

    print(Item('id1', 'id2', 10, 1))

if __name__ == '__main__':
    asyncio.run(main())