from collections.abc import Iterable

from stockx.api.base import StockXAPIBase
from stockx.models import (
    BatchStatus,
    BatchItemCreate,
    BatchItemDelete,
    BatchItemUpdate,
    BatchInputCreate,
    BatchInputUpdate,
)


class Batch(StockXAPIBase):

    async def create_listings(
            self,
            items: Iterable[BatchInputCreate],
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
            status: str | None = None
    ) -> list[BatchItemCreate]:
        params = {'status': status}
        response = await self.client.get(
            f'/batch/create-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchItemCreate.from_json(item) for item in items]

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

    async def listing_deletion_items(
            self,
            batch_id: str,
            status: str | None = None
    ) -> list[BatchItemDelete]:
        params = {'status': status}
        response = await self.client.get(
            f'/batch/delete-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchItemDelete.from_json(item) for item in items]

    async def update_listings(
            self,
            items: Iterable[BatchInputUpdate],
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
            status: str | None = None
    ) -> list[BatchItemUpdate]:
        params = {'status': status}
        response = await self.client.get(
            f'/batch/update-listing/{batch_id}/items',
            params=params,
        )
        items = response.data.get('items', [])
        return [BatchItemUpdate.from_json(item) for item in items]
