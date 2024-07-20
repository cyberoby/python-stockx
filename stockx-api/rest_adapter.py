import asyncio
import json
from typing import List, Dict, Union

import aiohttp

from exceptions import StockxApiException
from models import Response

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

class RestAdapter:
    
    def __init__(
            self,
            hostname: str,
            version: str,
            _verify_ssl: bool = True,
    ) -> None:
        self.url = f'https://{hostname}/{version}'
        self._verify_ssl = _verify_ssl
        if not _verify_ssl:
            pass    # Todo: ssl verification for aiohttp

        self._session: aiohttp.ClientSession = None
        self._refresh_task: asyncio.Task = None

    async def initialize(self) -> None:
        self._refresh_task = asyncio.create_task(self._refresh_session())
        await asyncio.sleep(1)

    async def close(self) -> None:
        if self._session:
            await self._session.close()
        if self._refresh_task:
            self._refresh_task.cancel()
    
    async def _do(
            self, 
            method: str,
            endpoint: str, 
            params: dict = None,
            data: dict = None
    ) -> Response:
        url = f'{self.url}{endpoint}'
        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=data,  
                verify_ssl = self._verify_ssl
            ) as response:
                res = await response.json()
                if 299 >= response.status >= 200:
                    return Response(status_code=response.status, 
                                    message=response.reason, data=res)
                raise Exception(res['message'])
        except aiohttp.ClientError as e:
            raise StockxApiException('Request failed') from e
        
    async def get(
            self, endpoint: str, params: dict = None
    ) -> Response:
        return await self._do('GET', endpoint, params=params)
    
    async def post(
            self, endpoint: str, params: dict = None, data: dict = None
    ) -> Response:
        return await self._do('POST', endpoint, params=params, data=data)

    async def delete(
            self, endpoint: str, params: dict = None
    ) -> Response:
        return await self._do('DELETE', endpoint, params=params)
        

    async def _refresh_session(self) -> None:
        while True:
            if self._session: 
                await self._session.close()
            headers = await self._refresh_token()
            self._session = aiohttp.ClientSession(headers=headers)
            await asyncio.sleep(REFRESH_TIME)

    async def _refresh_token(self) -> dict:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        refresh_data = {
            'grant_type': GRANT_TYPE,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'audience': AUDIENCE,
            'refresh_token': REFRESH_TOKEN
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(REFRESH_URL, headers=headers, 
                                    data=refresh_data) as response:
                payload = await response.json()
                token = payload['access_token']
                return {
                    'Authorization': f'Bearer {token}',
                    'x-api-key': X_API_KEY
                }


async def main() -> None:
    rest = RestAdapter(HOSTNAME, VERSION)
    await rest.initialize()

    r = await rest.get('/selling/orders/active')
    print(r)
    await rest.close()


asyncio.run(main())

            