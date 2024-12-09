import asyncio
from collections.abc import (
    Awaitable,
    Callable,
    Iterable,
)

from .base import StockXAPIBase
from ..errors import StockXBatchTimeout
from ..models import (
    BatchStatus,
    BatchCreateResult,
    BatchDeleteResult,
    BatchUpdateResult,
    BatchCreateInput,
    BatchUpdateInput,
)


class Batch(StockXAPIBase):
    """Interface for creating, updating, and deleting listings in batches."""

    async def create_listings(
            self,
            items: Iterable[BatchCreateInput],
    ) -> BatchStatus:
        """Create multiple listings in a batch operation."""
        data = {'items': [item.to_json() for item in items]}
        response = await self.client.post(
           endpoint='/selling/batch/create-listing', 
           data=data
        )
        return BatchStatus.from_json(response.data)

    async def create_listings_status(
            self,
            batch_id: str,
    ) -> BatchStatus:
        """Get status of a batch create operation."""
        response = await self.client.get(
            endpoint=f'/selling/batch/create-listing/{batch_id}'
        )
        return BatchStatus.from_json(response.data)
    
    async def create_listings_items(
            self,
            batch_id: str,
            *,
            status: str | None = None,
    ) -> list[BatchCreateResult]:
        """Get item-level results for items in a batch create operation."""
        params = {'status': status}
        response = await self.client.get(
            endpoint=f'/selling/batch/create-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchCreateResult.from_json(item) for item in items]
    
    async def create_listings_completed(
            self, 
            batch_ids: Iterable[str], 
            timeout: int,
    ) -> None:
        """Wait for batch create operations to complete.
        
        Raises
        ------
        `StockXBatchTimeout`
            If batch operations don't complete within timeout
        """
        await batch_completed(batch_ids, self.create_listings_status, timeout)

    async def delete_listings(
            self,
            listing_ids: Iterable[str],
    ) -> BatchStatus:
        """Delete multiple listings in a batch operation."""
        data = {'items': [{'listingId': id} for id in listing_ids]}
        response = await self.client.post(
            endpoint='/selling/batch/delete-listing', 
            data=data
        )
        return BatchStatus.from_json(response.data)

    async def delete_listings_status(
            self,
            batch_id: str,
    ) -> BatchStatus:
        """Get status of a batch delete operation."""
        response = await self.client.get(
            endpoint=f'/selling/batch/delete-listing/{batch_id}'
        )
        return BatchStatus.from_json(response.data)

    async def delete_listings_items(
            self,
            batch_id: str,
            *,
            status: str | None = None,
    ) -> list[BatchDeleteResult]:
        """Get item-level results for items in a batch delete operation."""
        params = {'status': status}
        response = await self.client.get(
            endpoint=f'/selling/batch/delete-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchDeleteResult.from_json(item) for item in items]
    
    async def delete_listings_completed(
            self,
            batch_ids: Iterable[str], 
            timeout: int,
    ) -> None:
        """Wait for batch delete operations to complete.
        
        Raises
        ------
        `StockXBatchTimeout`
            If batch operations don't complete within timeout
        """
        await batch_completed(batch_ids, self.delete_listings_status, timeout)

    async def update_listings(
            self,
            items: Iterable[BatchUpdateInput],
    ) -> BatchStatus:
        """Update multiple listings in a batch operation."""
        data = {'items': [item.to_json() for item in items]}
        response = await self.client.post(
            endpoint='/selling/batch/update-listing', 
            data=data
        )
        return BatchStatus.from_json(response.data)

    async def update_listings_status(
            self,
            batch_id: str,
    ) -> BatchStatus:
        """Get status of a batch update operation."""
        response = await self.client.get(
            endpoint=f'/selling/batch/update-listing/{batch_id}'
        )
        return BatchStatus.from_json(response.data)

    async def update_listings_items(
            self,
            batch_id: str,
            *,
            status: str | None = None,
    ) -> list[BatchUpdateResult]:
        """Get item-level results for items in a batch update operation."""
        params = {'status': status}
        response = await self.client.get(
            endpoint=f'/selling/batch/update-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchUpdateResult.from_json(item) for item in items]
    
    async def update_listings_completed(
            self,
            batch_ids: Iterable[str], 
            timeout: int,
    ) -> None:
        """Wait for batch update operations to complete.
        
        Raises
        ------
        `StockXBatchTimeout`
            If batch operations don't complete within timeout
        """
        await batch_completed(batch_ids, self.update_listings_status, timeout)
    
    
async def batch_completed(
        batch_ids: Iterable[str], 
        get_batch_status: Callable[[str], Awaitable[BatchStatus]], 
        timeout: int,
) -> None:
    """Wait for batch operations to complete with exponential backoff.

    Parameters
    ----------
    batch_ids : `Iterable[str]`
        Batch operation IDs to monitor
    get_batch_status : `Callable[[str], Awaitable[BatchStatus]]`
        Get batch status callback to use
    timeout : `int`
        Maximum wait time in seconds

    Raises
    ------
    `StockXBatchTimeout`
        If batch operations don't complete within timeout
    """
    finished_batch_ids = set()
    pending_batch_ids = set(batch_ids)

    sleep, waited = 1, 0
    while waited <= timeout:
        await asyncio.sleep(sleep)

        for batch_id in pending_batch_ids:
            status = await get_batch_status(batch_id)
            if (
                status.item_statuses.completed
                + status.item_statuses.failed
                == status.total_items
            ):
                finished_batch_ids.add(batch_id)

        pending_batch_ids.difference_update(finished_batch_ids)
        if len(pending_batch_ids) == 0:
            return
        
        waited += sleep
        sleep = min(sleep * 2, timeout - waited)
    else:
        raise StockXBatchTimeout(
            message='Batch operation timed out.', 
            batch_ids=pending_batch_ids
        )

