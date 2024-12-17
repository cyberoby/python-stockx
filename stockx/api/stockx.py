from __future__ import annotations

from .batch import Batch
from .catalog import Catalog
from .client import StockXAPIClient
from .listings import Listings
from .orders import Orders
from ..errors import StockXNotInitialized
from ..logs import logger


class StockX:
    """Main interface for interacting with the StockX API.

    Parameters
    ----------
    client : StockXAPIClient
        The API client used for making requests to StockX.

    Attributes
    ----------
    batch : `Batch`
        Interface for batch listing operations.
    catalog : `Catalog`
        Interface for product catalog operations.
    listings : `Listings`
        Interface for listing operations.
    orders : `Orders`
        Interface for viewing sales orders.

    Notes
    -----
    This class must be initialized with a valid StockXAPIClient and logged in
    before accessing any endpoints. It is recommended to use this class as an
    async context manager.

    Examples
    --------
    >>> client = StockXAPIClient(...)
    >>> async with StockX(client) as stockx:
    ...     # Access API endpoints
    ...     await stockx.catalog.get_product(...)
    ...     await stockx.listings.create_listing(...)
    """

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
        """Login to the StockX API."""
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
        """Close and logout from the StockX API."""
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.error(f'Error while logging out of StockX API: {e}')
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
        