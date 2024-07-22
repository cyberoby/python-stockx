from datetime import datetime
from typing import AsyncIterator

from stockx.api.base import StockXAPI
from stockx.models.core import Listing, ListingPartial, Operation


class Listings(StockXAPI):

    async def get_listing(
            self, 
            listing_id: str
    ) -> Listing:
        response = await self.client.get(
            f'/selling/listings/{listing_id}'
        )
        return Listing.from_json(response.data)

    async def get_all_listings(
            self,
            product_ids: list[str] = None,
            variant_ids: list[str] = None,
            from_date: datetime = None,
            to_date: datetime = None,
            listing_statuses: list[str] = None,
            inventory_types: list[str] = None,
            limit: int = None,
            page_size: int = 10
    ) -> AsyncIterator[ListingPartial]:
        params = {
            'productIds': ','.join(product_ids) if product_ids else None,
            'variantIds': ','.join(variant_ids) if variant_ids else None,
            'fromDate': str(datetime.date(from_date)) if from_date else None,
            'toDate': str(datetime.date(to_date)) if to_date else None,
            'listingStatuses': ','.join(listing_statuses) if listing_statuses else None,
            'inventoryTypes': ','.join(inventory_types) if inventory_types else None
        }
        async for listing in self._page(
            endpoint='/selling/listings',
            results_key='listings',
            params=params,
            limit=limit,
            page_size=page_size
        ):
            yield ListingPartial.from_json(listing)

    async def create_listing(
            self,
            amount: float
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

