from typing import AsyncIterator

from stockx.api.base import StockXAPI
from stockx.models.core import Listing, Operation


class Listings(StockXAPI):

    async def get_listing(
            self, 
            listing_id: str
    ) -> Listing:
        pass

    async def get_all_listings(
            self,
    ) -> AsyncIterator[Listing]:
        pass

    async def create_listing(
            self,
    ) -> Operation:
        pass

    async def activate_listing(
            self, 
            listing_id: str,
    ) -> Operation:
        pass

    async def deactivate_listing(
            self, 
            listing_id: str
    ) -> Operation:
        pass

    async def update_listing(
            self,
            listing_id: str,
    ) -> Operation:
        pass

    async def delete_listing(
            self, 
            listing_id: str
    ) -> Operation:
        pass
    
    async def get_listing_operation(
            self, 
            listing_id: str, 
            operation_id: str
    ) -> Operation:
        pass

    async def get_all_listing_operations(
            self,
            listing_id: str
    ) -> AsyncIterator[Operation]:
        pass

