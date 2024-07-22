from stockx.api.base import StockXAPI
from stockx.models.core import Batch


class Batch(StockXAPI):

    async def listings_creation(
            self,
    ) -> Batch:
        pass

    async def listings_creation_status(
            self,
            batch_id: str
    ) -> Batch:
        pass
    
    async def listings_creation_items(
            self,
            batch_id: str,
            listing_status: str = None
    ) -> list:
        pass

    async def listings_deletion(
            self,
    ) -> Batch:
        pass

    async def listings_deletion_status(
            self,
            batch_id: str
    ) -> Batch:
        pass

    async def listing_deletion_items(
            self,
            batch_id: str,
            status: str = None
    ) -> list:
        pass

    async def listing_update(
            self,
    ) -> Batch:
        pass

    async def listing_update_status(
            self,
            batch_id: str
    ) -> Batch:
        pass

    async def listing_update_items(
            self,
            batch_id: str,
            listing_status: str = None
    ) -> list:
        pass
