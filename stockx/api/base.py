from typing import AsyncIterator

from stockx.api.client import StockXAPIClient

# TODO: fix type hints
class StockXAPIBase:

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
        params = self._set_params(params, page_size)
        page_number = 1
        count = 0

        while self._check(count, limit):
            params['pageNumber'] = page_number
            response = await self.client.get(endpoint, params=params)
            has_next_page = bool(response.data.get('hasNextPage', False))
            results = response.data.get(results_key, [])

            for item in results:
                yield item
                count += 1
                if not self._check(count, limit):
                    break

            if not has_next_page: 
                break
            page_number += 1

    async def _page_cursor(
            self, 
            endpoint: str,
            results_key: str,
            params: dict = None, 
            limit: int = None, 
            page_size: int = 10
    ) -> AsyncIterator[dict]:
        params = self._set_params(params, page_size)
        count = 0

        while self._check(count, limit):
            response = await self.client.get(endpoint, params=params)
            next_cursor =  str(response.data.get('nextCursor'))
            results = response.data.get(results_key, [])

            for item in results:
                yield item
                count += 1
                if not self._check(count, limit):
                    break
            
            if not next_cursor:
                break
            params['cursor'] = next_cursor

    @staticmethod
    def _check(count: int, limit: int) -> bool:
        return count < limit if limit else True
    
    @staticmethod
    def _set_params(params: dict, page_size: int) -> dict:
        params = params if params else {}
        params['pageSize'] = page_size
        return params



