from math import ceil
from typing import AsyncIterator

from .client import StockXAPIClient
from ..types import JSON, Params


class StockXAPIBase:
    """Base class for StockX API endpoints.
    
    Parameters
    ----------
    client : `StockXAPIClient`
        StockX API client instance for making requests
    """
    
    def __init__(self, client: StockXAPIClient) -> None:
        self.client = client
     
    async def _page(
            self, 
            endpoint: str,
            results_key: str,
            params: Params | None = None, 
            limit: int | None = None, 
            page_size: int = 10,
            reverse: bool = False,
    ) -> AsyncIterator[JSON]:
        """Paginate through API results."""

        params = params if params else {}
        params['pageSize'] = page_size

        if reverse:
            response = await self.client.get(endpoint, params=params)
            page_number = ceil(response.data.get('count', 0) / page_size) or 1
        else:
            page_number = 1

        count = 0

        while check(count, limit):
            params['pageNumber'] = page_number
            response = await self.client.get(endpoint, params=params)

            if reverse:
                has_next_page = page_number > 1
            else:
                has_next_page = bool(response.data.get('hasNextPage', False))

            results = response.data.get(results_key, [])
            if reverse:
                results = reversed(results)

            for item in results:
                yield item
                count += 1
                if not check(count, limit):
                    break

            if not has_next_page: 
                break

            page_number += 1 if not reverse else -1

    async def _page_cursor(
            self, 
            endpoint: str,
            results_key: str,
            params: Params | None = None, 
            limit: int | None = None, 
            page_size: int = 10
    ) -> AsyncIterator[JSON]:
        """Paginate through API results using cursor pagination."""
        
        params = params if params else {}
        params['pageSize'] = page_size
        count = 0

        while check(count, limit):
            response = await self.client.get(endpoint, params=params)
            next_cursor =  str(response.data.get('nextCursor'))
            results = response.data.get(results_key, [])

            for item in results:
                yield item
                count += 1
                if not check(count, limit):
                    break
            
            if not next_cursor:
                break
            params['cursor'] = next_cursor


def check(count: int, limit: int | None) -> bool:
    """Check if the number of results has reached the limit."""
    return count < limit if limit is not None else True



