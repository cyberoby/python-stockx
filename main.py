import asyncio


async def main():

    async def async_new_price():
        return 10
    
    def new_price():
        return 100
    
    price = 10
    
    price()
    
    try:
        print(await new_price())
    except TypeError:
        print(new_price())

if __name__ == '__main__':
    asyncio.run(main())