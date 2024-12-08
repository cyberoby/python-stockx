from __future__ import annotations
import aiohttp
import asyncio
from collections.abc import Mapping, Sequence

from .retry import retry
from .throttle import throttle
from ...exceptions import (
    StockXNotInitialized,
    stockx_request_error,
)
from ...models import Response


GRANT_TYPE = 'refresh_token'
REFRESH_URL = 'https://accounts.stockx.com/oauth/token'
REFRESH_TOKEN_SLEEP = 3600
AUDIENCE = 'gateway.stockx.com'


JSONPrimitive = str | int | float | bool | None
Params = Mapping[str, JSONPrimitive]
type JSON = Mapping[str, JSONPrimitive | Sequence[JSONPrimitive] | JSON]


class StockXAPIClient:
    """Interface for making HTTP requests to StockX API."""
    
    def __init__(
            self,
            hostname: str,
            version: str,
            x_api_key: str,
            client_id: str,
            client_secret: str,
            refresh_token: str,
    ) -> None:
        self.url = f'https://{hostname}/{version}'
        self.x_api_key = x_api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        
        self._auth_headers: dict[str, str] | None = None
        self._refresh_task: asyncio.Task | None = None
        self._session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Initialize and login client."""
        if not self._session and not self._refresh_task:
            self._session = aiohttp.ClientSession()
            self._refresh_task = asyncio.create_task(self._refresh_token())
            await asyncio.sleep(1)

    async def close(self) -> None:
        """Close client session."""
        if self._session:
            await self._session.close()
        if self._refresh_task:
            self._refresh_task.cancel()
        
    async def get(self, endpoint: str, params: Params | None = None) -> Response:
        """Perform `GET` request."""
        return await self._do('GET', endpoint, params=params)
    
    async def put(self, endpoint: str, data: JSON | None = None) -> Response:
        """Perform `PUT` request."""
        return await self._do('PUT', endpoint, data=data)
    
    async def post(self, endpoint: str, data: JSON | None = None) -> Response:
        """Perform `POST` request."""
        return await self._do('POST', endpoint, data=data)

    async def patch(self, endpoint: str, data: JSON | None = None) -> Response:
        """Perform `PATCH` request."""
        return await self._do('PATCH', endpoint, data=data)
    
    async def delete(self, endpoint: str) -> Response:
        """Perform `DELETE` request."""
        return await self._do('DELETE', endpoint)
    
    @throttle(seconds=3)
    @retry(max_attempts=5, initial_delay=2, timeout=60)
    async def _do(
            self, 
            method: str,
            endpoint: str, 
            params: Params | None = None,
            data: JSON | None = None
    ) -> Response:
        if not self._auth_headers:
            raise StockXNotInitialized()
        
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        if data:
            data = {k: v for k, v in data.items() if v is not None}

        url = f'{self.url}{endpoint}'
        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=data,
                headers=self._auth_headers
            ) as response:
                data = await response.json()
                if 299 >= response.status >= 200:
                    return Response(
                        status_code=response.status, 
                        message=response.reason, 
                        data=data
                    )
                raise stockx_request_error(
                    message=data.get('errorMessage', None), 
                    status_code=response.status
                )
        except aiohttp.ClientResponseError as e:
            raise stockx_request_error(e.message, e.status) from e
        except aiohttp.ClientError as e:
            raise stockx_request_error('Request failed.') from e
            
    async def _refresh_token(self) -> None:
        while True:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            auth_data = {
                'grant_type': GRANT_TYPE,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'audience': AUDIENCE,
                'refresh_token': self.refresh_token
            }
            async with self._session.post(
                REFRESH_URL, headers=headers, data=auth_data
            ) as response:
                payload = await response.json()
                token = payload['access_token']
                self._auth_headers = {
                    'Authorization': f'Bearer {token}',
                    'x-api-key': self.x_api_key
                }
                
            await asyncio.sleep(REFRESH_TOKEN_SLEEP)
        
            

            