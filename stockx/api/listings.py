import asyncio
from collections.abc import AsyncIterator, Iterable
from datetime import datetime

from .base import StockXAPIBase
from ..format import (
    comma_separated,
    iso,
    iso_date,
)
from ..models import (
    Currency,
    Listing,
    ListingDetail,
    ListingStatus, 
    Operation,
    OperationStatus,
)


class Listings(StockXAPIBase):
    """Interface for interacting with listings."""

    async def get_listing(
            self, 
            listing_id: str
    ) -> ListingDetail:
        """Get a listing by its ID."""
        response = await self.client.get(f'/selling/listings/{listing_id}')
        return ListingDetail.from_json(response.data)

    async def get_all_listings(
            self,
            product_ids: Iterable[str] | None = None,
            variant_ids: Iterable[str] | None = None,
            from_date: datetime | None = None,
            to_date: datetime | None = None,
            listing_statuses: Iterable[ListingStatus] | None = None,
            inventory_types: Iterable[str] | None = None,          
            limit: int | None = None,  
            page_size: int = 10,
            oldest_first: bool = False,
    ) -> AsyncIterator[Listing]:
        """Get all listings."""
        params = {
            'productIds': comma_separated(product_ids),
            'variantIds': comma_separated(variant_ids),
            'fromDate': iso_date(from_date),
            'toDate': iso_date(to_date),
            'listingStatuses': comma_separated(
                status.value for status in listing_statuses
            ) if listing_statuses else None,
            'inventoryTypes': comma_separated(inventory_types),
        }
        async for listing in self._page(
            endpoint='/selling/listings',
            results_key='listings',
            params=params,
            limit=limit,
            page_size=page_size,
            reverse=oldest_first,
        ):
            yield Listing.from_json(listing)

    async def create_listing(
            self,
            amount: float,
            variant_id: str,
            currency: Currency | None = None,
            expires_at: datetime | None = None,
            active: bool | None = None
    ) -> Operation:
        """Create a listing."""
        data = {
            'amount': f'{amount:.0f}',
            'variantId': variant_id,
            'currencyCode': currency.value if currency else None,
            'expiresAt': iso(expires_at),
            'active': active,
        }
        response = await self.client.post(f'/selling/listings', data=data)
        return Operation.from_json(response.data)

    async def activate_listing(
            self, 
            listing_id: str,
            amount: float,   # TODO required???
            currency: Currency | None = None,
            expires_at: datetime | None = None
    ) -> Operation:
        """Activate a listing."""
        data = {
            'amount': f'{amount:.0f}',
            'currencyCode': currency.value if currency else None,
            'expiresAt': iso(expires_at),
        }
        response = await self.client.put(
            f'/selling/listings/{listing_id}/activate', data=data
        )
        return Operation.from_json(response.data)

    async def deactivate_listing(
            self, 
            listing_id: str
    ) -> Operation:
        """Deactivate a listing."""
        response = await self.client.put(
            f'/selling/listings/{listing_id}/deactivate'
        )
        return Operation.from_json(response.data)

    async def update_listing(
            self,
            listing_id: str,
            amount: float | None = None,
            currency: Currency | None = None,
            expires_at: datetime | None = None,
    ) -> Operation:
        """Update a listing."""
        data = {
            'amount': f'{amount:.0f}',
            'currencyCode': currency.value if currency else None,
            'expiresAt': iso(expires_at),
        }
        response = await self.client.patch(
            f'/selling/listings/{listing_id}', data=data
        )
        return Operation.from_json(response.data)

    async def delete_listing(
            self, 
            listing_id: str
    ) -> Operation:
        """Delete a listing."""
        response = await self.client.delete(f'/selling/listings/{listing_id}')
        return Operation.from_json(response.data)
    
    async def get_listing_operation(
            self, 
            listing_id: str, 
            operation_id: str
    ) -> Operation:
        """Get a listing operation by its ID."""
        response = await self.client.get(
            f'/selling/listings/{listing_id}/operations/{operation_id}'
        )
        return Operation.from_json(response.data)

    async def get_all_listing_operations(
            self,
            listing_id: str,
            limit: int = None,
            page_size: int = 10
    ) -> AsyncIterator[Operation]:
        """Get all operations for a listing."""
        async for operation in self._page_cursor(
            endpoint=f'/selling/listings/{listing_id}/operations',
            results_key='operations',
            limit=limit,
            page_size=page_size
        ):
            yield Operation.from_json(operation)

    async def operation_succeeded(
            self,
            operation: Operation
    ) -> bool:
        """Check if a listing operation has succeeded."""
        while operation.status == OperationStatus.PENDING:
            operation = await self.get_listing_operation(
                listing_id=operation.listing_id,
                operation_id=operation.id
            )
        
        if operation.status == OperationStatus.FAILED:
            return False
        
        return True

