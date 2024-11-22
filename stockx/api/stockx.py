from .client import StockXAPIClient
from .batch import Batch
from .catalog import Catalog
from .listings import Listings
from .orders import Orders
from ..exceptions import StockXAuthError


class StockX:

    __slots__ = (
        '_batch', 
        '_client', 
        '_catalog', 
        '_listings', 
        '_orders', 
        'version',
    )

    def __init__(self, version: str) -> None:
        self.version = version
        self._batch = None

    async def login(
            self,
            x_api_key: str,
            client_id: str,
            client_secret: str,
            refresh_token: str
    ) -> None:
        self._client = StockXAPIClient(
            hostname='api.stockx.com', 
            version=self.version, 
            x_api_key=x_api_key, 
            client_id=client_id, 
            client_secret=client_secret
        )

        await self._client.initialize(refresh_token)

        self._batch = Batch(self._client)
        self._catalog = Catalog(self._client)
        self._listings = Listings(self._client)
        self._orders = Orders(self._client)

    @property
    def batch(self) -> Batch:
        return self._get('batch')
        
    @property
    def catalog(self) -> Catalog:
        return self._get('catalog')
        
    @property
    def listings(self) -> Listings:
        return self._get('listings')
        
    @property
    def orders(self) -> Orders:
        return self._get('orders')
        
    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    def _get(self, api):
        try:
            return getattr(self, f'_{api}')
        except AttributeError:
            raise StockXAuthError(
                f'{self.__class__.__name__} is not logged in. '
                f'Unable to access {api}.'
            )
        