import aiohttp
import asyncio

from ...exceptions import StockXAPIException
from ...models import Response

TOKEN = '***REMOVED***'
GRANT_TYPE = 'refresh_token'
CLIENT_ID = '***REMOVED***'
CLIENT_SECRET = '***REMOVED***'
X_API_KEY = '***REMOVED***'
REFRESH_TOKEN = '***REMOVED***'
REFRESH_URL = 'https://accounts.stockx.com/oauth/token'
REFRESH_TIME = 3600
AUDIENCE = 'gateway.stockx.com'
HOSTNAME = 'api.stockx.com'
VERSION = 'v2'


class StockXAPIClient:
    
    def __init__(
            self,
            hostname: str,
            version: str,
            x_api_key: str,
            client_id: str,
            client_secret: str, # TODO: maybe move last 3 attr to login()
    ) -> None:
        self.url = f'https://{hostname}/{version}'
        self.x_api_key = x_api_key
        self.client_id = client_id
        self.client_secret = client_secret
        
        self._is_initialized: bool = False
        self._session: aiohttp.ClientSession = None
        self._refresh_task: asyncio.Task = None

    async def initialize(self, refresh_token: str) -> None:
        refresh = self._refresh_session(refresh_token)
        self._refresh_task = asyncio.create_task(refresh)
        await asyncio.sleep(2)

    async def close(self) -> None:
        if self._session:
            await self._session.close()
        if self._refresh_task:
            self._refresh_task.cancel()
        
    async def get(self, endpoint: str, params: dict = None) -> Response:
        return await self._do('GET', endpoint, params=params)
    
    async def put(self, endpoint: str, data: dict = None) -> Response:
        return await self._do('PUT', endpoint, data=data)
    
    async def post(self, endpoint: str, data: dict = None) -> Response:
        return await self._do('POST', endpoint, data=data)

    async def patch(self, endpoint: str, data: dict = None) -> Response:
        return await self._do('PATCH', endpoint, data=data)
    
    async def delete(self, endpoint: str) -> Response:
        return await self._do('DELETE', endpoint)
    
    async def _do(
            self, 
            method: str,
            endpoint: str, 
            params: dict = None,
            data: dict = None
    ) -> Response:
        if not self._is_initialized:
            raise StockXAPIException('Client must be initialized before making requests.')
        
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
                json=data
            ) as response:
                data = await response.json()
                if 299 >= response.status >= 200:
                    return Response(
                        status_code=response.status, 
                        message=response.reason, 
                        data=data
                    )
                raise Exception(f'{data=} {response.reason=} {response.status=}') # TODO: should include response object in the exception?
        except aiohttp.ClientError as e:
            raise StockXAPIException('Request failed') from e # TODO custom exceptions
        
    async def _refresh_session(self, refresh_token: str) -> None:
        while True:
            if self._session: 
                await self._session.close() # TODO: don't close session, just change token
            headers = await self._login(refresh_token)
            self._session = aiohttp.ClientSession(headers=headers) 
            self._is_initialized = True
            await asyncio.sleep(REFRESH_TIME)

    async def _login(self, refresh_token: str) -> dict:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        refresh_data = {
            'grant_type': GRANT_TYPE,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'audience': AUDIENCE,
            'refresh_token': refresh_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                REFRESH_URL, headers=headers, data=refresh_data
            ) as response:
                payload = await response.json()
                token = payload['access_token']
                return {
                    'Authorization': f'Bearer {token}',
                    'x-api-key': self.x_api_key
                }
            

            