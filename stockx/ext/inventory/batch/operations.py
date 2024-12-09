from __future__ import annotations

from collections.abc import (
    Callable, 
    Iterable, 
    Iterator,
)
from itertools import chain
from typing import TYPE_CHECKING

from .inputs import (
    create_listings_inputs,
    delete_listings_inputs,
    update_listings_inputs,
    sync_listings_inputs,
)
from .results import UpdateResult
from ..item import Item, ListedItem
from ....api import StockX
from ....errors import StockXBatchTimeout, StockXIncompleteOperation

if TYPE_CHECKING:
    from ....models import (
        BatchCreateInput,
        BatchCreateResult,
        BatchUpdateResult,
        BatchDeleteResult,
    )


async def update_quantity(
        stockx: StockX, 
        items: Iterable[ListedItem],
) -> Iterator[UpdateResult]:
    """Update listing quantities by creating or deleting listings as needed.
    
    Parameters
    ----------
    stockx : `StockX`
        StockX API interface
    items : `Iterable[ListedItem]`
        Items whose quantities need to be updated
        
    Returns
    -------
    `Iterator[UpdateResult]`
        Results of the update operation for each item
        
    Raises
    ------
    `StockXIncompleteOperation`
        If some batch operations timeout. The exception contains partial 
        results for operations that completed successfully.
    """
    decrease = {item for item in items if item.quantity_to_sync() < 0}
    increase = {item for item in items if item.quantity_to_sync() > 0}

    # Get listing IDs to delete
    delete_ids = (item.listing_ids[item.quantity_to_sync():] for item in decrease)

    timed_out_batch_ids = []  # Incomplete batch IDS

    try:
        deleted_results = await delete_listings(
            stockx=stockx, 
            listing_ids=chain.from_iterable(delete_ids)
        )
    except StockXIncompleteOperation as e:
        timed_out_batch_ids += e.timed_out_batch_ids
        deleted_results = e.partial_results

    try:
        increased_results = await increase_listings(
            stockx=stockx, 
            items=increase
        )
    except StockXIncompleteOperation as e:
        timed_out_batch_ids += e.timed_out_batch_ids
        increased_results = e.partial_results

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
            in increased_results if result.item == item
        )

    if timed_out_batch_ids:
        raise StockXIncompleteOperation(
            'Update quantity operation timed out. Partial results available.', 
            partial_results=chain(decreased_results, increased_results), 
            timed_out_batch_ids=timed_out_batch_ids
        )

    return chain(decreased_results, increased_results)


async def _create_listings(
        stockx: StockX,
        items: Iterable[Item | ListedItem],
        inputs_factory: Callable[..., Iterable[Iterable[BatchCreateInput]]],
        timeout: int = 60,
) -> Iterator[UpdateResult]:
    """Create listings in batches using the provided inputs factory."""
    batch_ids = []
    for inputs in inputs_factory(items, 'EUR', 100):
        batch_status = await stockx.batch.create_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    try:            
        create_results = await _batch_results(
            stockx=stockx, 
            batch_ids=batch_ids, 
            func=publish_listings, 
            timeout=timeout
        )
        return UpdateResult.from_batch_create(items, create_results)
    except StockXBatchTimeout as e:
        partial_results = UpdateResult.from_batch_create(
            items=items,
            results=e.partial_batch_results
        )
        raise StockXIncompleteOperation(
            'Batch create operation timed out. Partial results available.', 
            partial_results=partial_results, 
            timed_out_batch_ids=e.queued_batch_ids
        )
    

async def increase_listings(
        stockx: StockX,
        items: Iterable[ListedItem],
        timeout: int = 60,
) -> Iterator[UpdateResult]:
    """Bulk create additional listings for items that need increased quantity."""
    return await _create_listings(stockx, items, sync_listings_inputs, timeout)


async def publish_listings(
        stockx: StockX,
        items: Iterable[Item],
        timeout: int = 60,
) -> Iterator[UpdateResult]:
    """Bulk create new listings for items that haven't been listed yet.
    
    Parameters
    ----------
    stockx : `StockX`
        StockX API interface
    items : `Iterable[Item]`
        Items to create listings for
    timeout : `int`, default 60
        Maximum time to wait for batch operations to complete
        
    Returns
    -------
    `Iterator[UpdateResult]`
        Results of the create operation for each item
        
    Raises
    ------
    `StockXIncompleteOperation`
        If some batch operations timeout. The exception contains partial 
        results for operations that completed successfully.
    """
    return await _create_listings(stockx, items, create_listings_inputs, timeout)


async def update_listings(
        stockx: StockX,
        items: Iterable[ListedItem],
        timeout: int = 60,
) -> Iterator[UpdateResult]:
    """Bulk update existing listings with new prices.
    
    Parameters
    ----------
    stockx : `StockX`
        StockX API interface
    items : `Iterable[ListedItem]`
        Items whose listings need price updates
    timeout : `int`, default 60
        Maximum time to wait for batch operations to complete
        
    Returns
    -------
    `Iterator[UpdateResult]`
        Results of the update operation for each item
        
    Raises
    ------
    `StockXIncompleteOperation`
        If some batch operations timeout. The exception contains partial 
        results for operations that completed successfully.
    """
    batch_ids = []
    for inputs in update_listings_inputs(items, 'EUR', 100):
        batch_status = await stockx.batch.update_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    try:
        update_results = await _batch_results(
            stockx=stockx, 
            batch_ids=batch_ids, 
            func=update_listings, 
            timeout=timeout
        )
        return UpdateResult.from_batch_update(items, update_results)
    except StockXBatchTimeout as e:
        partial_results = UpdateResult.from_batch_update(
            items=items,
            results=e.partial_batch_results
        )
        raise StockXIncompleteOperation(
            'Batch update operation timed out. Partial results available.', 
            partial_results=partial_results, 
            timed_out_batch_ids=e.queued_batch_ids
        )


async def delete_listings(
        stockx: StockX,
        listing_ids: Iterable[str],
        timeout: int = 60,
) -> UpdateResult:
    """Bulk delete existing listings.
    
    Parameters
    ----------
    stockx : `StockX`
        StockX API interface
    listing_ids : `Iterable[str]`
        IDs of listings to delete
    timeout : `int`, default 60
        Maximum time to wait for batch operations to complete
        
    Returns
    -------
    `UpdateResult`
        Results of the delete operation
        
    Raises
    ------
    StockXIncompleteOperation
        If some batch operations timeout. The exception contains partial 
        results for operations that completed successfully.
    """
    batch_ids = []
    for inputs in delete_listings_inputs(listing_ids, 100):
        batch_status = await stockx.batch.delete_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    try:
        delete_results = await _batch_results(
            stockx=stockx, 
            batch_ids=batch_ids, 
            func=delete_listings, 
            timeout=timeout
        )
        return UpdateResult.from_batch_delete(delete_results)
    except StockXBatchTimeout as e:
        partial_results = UpdateResult.from_batch_delete(
            results=e.partial_batch_results
        )
        raise StockXIncompleteOperation(
            'Batch delete operation timed out. Partial results available.', 
            partial_results=partial_results, 
            timed_out_batch_ids=e.queued_batch_ids
        )

async def _batch_results(
        stockx: StockX, 
        batch_ids: Iterable[str], 
        func: publish_listings | update_listings | delete_listings, 
        timeout: int
) -> list[BatchCreateResult | BatchUpdateResult | BatchDeleteResult]:
    """Wait for batch operations to complete and retrieve results.
    
    Raises
    ------
    `StockXBatchTimeout`
        If batch operations don't complete within timeout
    """
    timeout_error = None

    if func is publish_listings:
        batch_completed = stockx.batch.create_listings_completed
        get_items = stockx.batch.create_listings_items
    elif func is update_listings:
        batch_completed = stockx.batch.update_listings_completed
        get_items = stockx.batch.update_listings_items
    elif func is delete_listings:
        batch_completed = stockx.batch.delete_listings_completed
        get_items = stockx.batch.delete_listings_items

    try:
        await batch_completed(batch_ids, timeout)
    except StockXBatchTimeout as e:
        timeout_error = e

    batch_results = []

    for batch_id in batch_ids:
        results = await get_items(batch_id)
        for result in results:
            if result.status != 'QUEUED':
                batch_results.append(result)

    if timeout_error:
        timeout_error.partial_batch_results = batch_results
        raise timeout_error

    return batch_results