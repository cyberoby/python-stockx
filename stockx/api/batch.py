import asyncio
from collections.abc import (
    Awaitable,
    Callable,
    Iterable,
)

from .base import StockXAPIBase
from ..exceptions import BatchTimeOutError
from ..models import (
    BatchStatus,
    BatchCreateResult,
    BatchDeleteResult,
    BatchUpdateResult,
    BatchCreateInput,
    BatchUpdateInput,
)


class Batch(StockXAPIBase):

    async def create_listings(
            self,
            items: Iterable[BatchCreateInput],
    ) -> BatchStatus:
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
        await batch_completed(batch_ids, self.create_listings_status, timeout)

    async def delete_listings(
            self,
            listing_ids = Iterable[str],
    ) -> BatchStatus:
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
        await batch_completed(batch_ids, self.delete_listings_status, timeout)

    async def update_listings(
            self,
            items: Iterable[BatchUpdateInput],
    ) -> BatchStatus:
        data = {'items': [item.to_json() for item in items]}
        print(data)
        response = await self.client.post(
            endpoint='/selling/batch/update-listing', 
            data=data
        )
        return BatchStatus.from_json(response.data)

    async def update_listings_status(
            self,
            batch_id: str,
    ) -> BatchStatus:
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
        await batch_completed(batch_ids, self.update_listings_status, timeout)
    
    
async def batch_completed(
        batch_ids: Iterable[str], 
        batch_status_coro: Callable[[str], Awaitable[BatchStatus]], 
        timeout: int,
) -> None:
    completed_batch_ids = set()
    pending_batch_ids = set(batch_ids)

    sleep, waited = 1, 0
    while waited <= timeout:
        await asyncio.sleep(sleep)

        for batch_id in pending_batch_ids:
            status = await batch_status_coro(batch_id)
            if status.item_statuses.completed == status.total_items:
                completed_batch_ids.add(batch_id)

        pending_batch_ids.difference_update(completed_batch_ids)
        if len(pending_batch_ids) == 0:
            print('COMPLETED!!!!!!')
            return
        
        waited += sleep
        sleep = min(sleep * 2, timeout - waited)
    else:
        raise BatchTimeOutError # TODO: add report on completed items??
