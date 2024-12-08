from __future__ import annotations

from collections.abc import (
    Callable, 
    Iterable, 
    Iterator,
)
from itertools import chain

from .inputs import (
    create_listings_inputs,
    delete_listings_inputs,
    update_listings_inputs,
    sync_listings_inputs,
)
from .results import UpdateResult
from ..item import Item, ListedItem
from ....api import StockX, Batch
from ....exceptions import StockXBatchTimeout
from ....models import BatchCreateInput


async def update_quantity(
        stockx: StockX, 
        items: Iterable[ListedItem],
) -> Iterator[UpdateResult]:
    decrease = {item for item in items if item.quantity_to_sync() < 0}
    increase = {item for item in items if item.quantity_to_sync() > 0}

    delete_ids = (item.listing_ids[item.quantity_to_sync():] for item in decrease)
    deleted_results = await delete_listings(stockx, chain.from_iterable(delete_ids))

    increased_results = await increase_listings(stockx, increase)

    # Convert to sets for faster lookup
    deleted_set = set(deleted_results.deleted)
    failed_set = set(deleted_results.failed)
    error_map = {err.listing_id: err for err in deleted_results.errors_detail}
    
    decreased_results = []
    for item in decrease:
        deleted =  {lid for lid in item.listing_ids if lid in deleted_set}
        failed = tuple(lid for lid in item.listing_ids if lid in failed_set)
        errors = tuple(error_map[lid] for lid in failed if lid in error_map)

        # Update item's listing_ids by removing successfully deleted IDs
        item.listing_ids = [l for l in item.listing_ids if l not in deleted]

        decreased_results.append(
            UpdateResult(
                item, 
                deleted=deleted, 
                failed=failed, 
                errors_detail=errors
            )
        )
    
    # Update listing_ids for items in increase based on created results
    for item in increase:
        item.listing_ids.extend(
            result.created for result 
            in increased_results if item == result.item
        )

    return chain(decreased_results, increased_results)


async def _create_listings(
        stockx: StockX,
        items: Iterable[Item | ListedItem],
        inputs_factory: Callable[..., Iterable[Iterable[BatchCreateInput]]],
) -> Iterator[UpdateResult]:
    batch_ids = []
    for inputs in inputs_factory(items, 'EUR', 100):
        batch_status = await stockx.batch.create_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    results = await _batch_results(stockx, batch_ids, publish_listings, 60)
    
    return UpdateResult.from_batch_create(items, results)
    

async def increase_listings(
        stockx: StockX,
        items: Iterable[ListedItem],
) -> Iterator[UpdateResult]:
    return await _create_listings(stockx, items, sync_listings_inputs)


async def publish_listings(
        stockx: StockX,
        items: Iterable[Item]
) -> Iterator[UpdateResult]:
    return await _create_listings(stockx, items, create_listings_inputs)


async def update_listings(
        stockx: StockX,
        items: Iterable[ListedItem]
) -> Iterator[UpdateResult]:
    batch_ids = []
    for inputs in update_listings_inputs(items, 'EUR', 100):
        batch_status = await stockx.batch.update_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    results = await _batch_results(stockx, batch_ids, update_listings, 60)

    return UpdateResult.from_batch_update(items, results)


async def delete_listings(
        stockx: StockX,
        listing_ids: Iterable[str]
) -> UpdateResult:
    batch_ids = []
    for inputs in delete_listings_inputs(listing_ids, 100):
        batch_status = await stockx.batch.delete_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    results = await _batch_results(stockx, batch_ids, delete_listings, 60)

    return UpdateResult.from_batch_delete(results)


async def _batch_results(stockx, batch_ids, func, timeout):
    b: Batch = stockx.batch
    action_map = {
        publish_listings: (b.create_listings_completed, b.create_listings_items),
        update_listings: (b.update_listings_completed, b.update_listings_items),
        delete_listings: (b.delete_listings_completed, b.delete_listings_items),
    }

    batch_completed, get_items = action_map[func]

    try:
        await batch_completed(batch_ids, timeout)
    except StockXBatchTimeout as err:
        pass

    return [
        result for batch_id in batch_ids
        for result in await get_items(batch_id, status='COMPLETED') # TODO: maybe retrieve others as well?
    ]