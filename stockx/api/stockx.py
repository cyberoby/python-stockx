from __future__ import annotations

from .batch import Batch
from .catalog import Catalog
from .client import StockXAPIClient
from .listings import Listings
from .orders import Orders
from ..exceptions import StockXNotInitialized


class StockX:

    __slots__ = (
        '_batch', 
        '_catalog', 
        '_initialized', 
        '_listings', 
        '_orders', 
        'client', 
    )

    def __init__(self, client: StockXAPIClient) -> None:
        self.client = client
        self._initialized: bool = False

    async def login(self) -> None:
        if self._initialized:
            return

        await self.client.initialize()

        self._batch = Batch(self.client)
        self._catalog = Catalog(self.client)
        self._listings = Listings(self.client)
        self._orders = Orders(self.client)

        self._initialized = True

    async def __aenter__(self) -> StockX:
        await self.login()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
        
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
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                # TODO: log Error while closing StockX client: {e=}
                pass
            finally:
                self.client = None
                self._initialized = False

    def _get(self, api):
        try:
            return getattr(self, f'_{api}')
        except AttributeError:
            raise StockXNotInitialized(
                f'{self.__class__.__name__} is not logged in. '
                f'Unable to access {api}.'
            )
        