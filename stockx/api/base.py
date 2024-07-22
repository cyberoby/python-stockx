import asyncio
from typing import AsyncIterator

from stockx.api.client import StockXAPIClient


class StockXAPI:

    def __init__(self, client: StockXAPIClient) -> None:
        self.client = client
     
    async def _page(
            self, 
            endpoint: str,
            results_key: str,
            params: dict = None, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[dict]:
        params = params if params is not None else {}
        current_page = 1
        count = 0
        check = lambda count, max: count < max if max is not None else True

        while check(count, limit):
            params['pageNumber'] = current_page
            params['pageSize'] = page_size

            response = await self.client.get(endpoint, params=params)

            current_page = int(response.data.get('pageNumber'))
            has_next_page = bool(response.data.get('hasNextPage', False))
            results = response.data.get(results_key, [])

            for item in results:
                yield item
                count += 1
                await asyncio.sleep(2)
                if not check(count, limit):
                    break

            if not has_next_page: 
                break


