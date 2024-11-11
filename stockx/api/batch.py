from collections.abc import Iterable

from stockx.api.base import StockXAPIBase
from stockx.models import (
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
        response = await self.client.post('/batch/create-listing', data=data)
        return BatchStatus.from_json(response.data)

    async def get_create_listings_status(
            self,
            batch_id: str,
    ) -> BatchStatus:
        response = await self.client.get(f'/batch/create-listing/{batch_id}')
        return BatchStatus.from_json(response.data)
    
    async def get_create_listings_items(
            self,
            batch_id: str,
            *,
            status: str | None = None
    ) -> list[BatchCreateResult]:
        params = {'status': status}
        response = await self.client.get(
            f'/batch/create-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchCreateResult.from_json(item) for item in items]

    async def delete_listings(
            self,
            listing_ids = Iterable[str],
    ) -> BatchStatus:
        data = {'items': [{'listingId': id} for id in listing_ids]}
        response = await self.client.post('/batch/delete-listing', data=data)
        return BatchStatus.from_json(response.data)

    async def get_delete_listings_status(
            self,
            batch_id: str
    ) -> BatchStatus:
        response = await self.client.get(f'/batch/delete-listing/{batch_id}')
        return BatchStatus.from_json(response.data)

    async def get_delete_listings_items(
            self,
            batch_id: str,
            *,
            status: str | None = None
    ) -> list[BatchDeleteResult]:
        params = {'status': status}
        response = await self.client.get(
            f'/batch/delete-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchDeleteResult.from_json(item) for item in items]

    async def update_listings(
            self,
            items: Iterable[BatchUpdateInput],
    ) -> BatchStatus:
        data = {'items': [item.to_json() for item in items]}
        response = await self.client.post('/batch/update-listing', data=data)
        return BatchStatus.from_json(response.data)

    async def get_update_listings_status(
            self,
            batch_id: str
    ) -> BatchStatus:
        response = await self.client.get(f'/batch/update-listing/{batch_id}')
        return BatchStatus.from_json(response.data)

    async def get_update_listings_items(
            self,
            batch_id: str,
            *,
            status: str | None = None
    ) -> list[BatchUpdateResult]:
        params = {'status': status}
        response = await self.client.get(
            f'/batch/update-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchUpdateResult.from_json(item) for item in items]
