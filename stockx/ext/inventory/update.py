from __future__ import annotations

from collections.abc import Iterable, Iterator
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import (
    groupby, 
    batched, 
    chain,
)
from typing import TypeAlias

from .item import Item
from ...api import StockX, Batch
from ...exceptions import BatchTimeOutError
from ...models import (
    BatchCreateInput,
    BatchCreateResult,
    BatchUpdateInput,
    BatchUpdateResult,
    BatchDeleteResult,
)
from ...processing import group_and_sum


BatchResult: TypeAlias = BatchCreateResult | BatchDeleteResult | BatchUpdateResult


@dataclass(slots=True, frozen=True)
class ErrorDetail:
    message: str
    occurrences: int
    listing_id: str | None = None

    @classmethod
    def from_results(
        cls, 
        results: Iterable[BatchResult],
        include_listing_id: bool = False
    ) -> Iterator[ErrorDetail]:
        if not include_listing_id:
            errors = (result.error for result in results if result.error)
            for message, occurrences in Counter(errors).items():
                yield cls(message, occurrences) 
        else:
            errors_ids = (
                (result.error, result.listing_input.listing_id)
                for result in results if result.error
            )
            for message, listing_id in errors_ids:
                yield cls(message, 1, listing_id)

    @classmethod
    def from_messages(cls, errors: Iterable[str]) -> Iterator[ErrorDetail]:
        for message, occurrences in Counter(errors).items():
            yield cls(message, occurrences)


@dataclass(slots=True, frozen=True)
class UpdateResult:
    item: Item | None = None
    created: tuple[str, ...] = field(default_factory=tuple)
    updated: tuple[str, ...] = field(default_factory=tuple)
    deleted: tuple[str, ...] = field(default_factory=tuple)
    failed: tuple[str, ...] = field(default_factory=tuple)
    errors_detail: tuple[ErrorDetail, ...] = field(default_factory=tuple)

    @classmethod
    def consolidate(
            cls, 
            *results: Iterable[UpdateResult]
    ) -> Iterator[UpdateResult]:
        results_ = chain(*results)

        # Group results by item
        grouped_results: defaultdict[Item, list[UpdateResult]] = defaultdict(list)
        for result in results_:
            grouped_results[result.item].append(result)

        for item, item_results in grouped_results.items():
            # Sets for each lifecycle stage to ensure latest status
            created_ids = set(chain.from_iterable(r.created for r in item_results))
            updated_ids = set(chain.from_iterable(r.updated for r in item_results))
            deleted_ids = set(chain.from_iterable(r.deleted for r in item_results))
            failed_ids = set(chain.from_iterable(r.failed for r in item_results))

            # Consolidate errors
            all_errors = chain.from_iterable(r.errors_detail for r in item_results)
            messages = (error.message for error in all_errors)
            unique_errors_detail = tuple(ErrorDetail.from_messages(messages))

            # Apply lifecycle rules:
            # 1. Move 'created' -> 'updated' if also in updated
            # 2. Move 'created' -> 'deleted' if also in deleted
            # 3. Move 'updated' -> 'deleted' if in both
            # 4. Remove from 'failed' if in created, updated, or deleted
            created_ids -= updated_ids | deleted_ids
            updated_ids -= deleted_ids
            failed_ids -= (created_ids | updated_ids | deleted_ids)

            yield cls(
                item=item,
                created=tuple(created_ids),
                updated=tuple(updated_ids),
                deleted=tuple(deleted_ids),
                failed=tuple(failed_ids),
                errors_detail=unique_errors_detail,
            ) 

    @classmethod
    def from_batch_update(
            cls,
            items: Iterable[Item],
            results: Iterable[BatchUpdateResult],
    ) -> Iterator[UpdateResult]:
        error_map = {r.listing_input.listing_id: r.error for r in results}

        for item in items:
            updated = (lid for lid in item.listing_ids if not error_map[lid])
            failed = (lid for lid in item.listing_ids if error_map[lid])
            errors = (error_map[listing_id] for listing_id in failed)
            errors_detail = ErrorDetail.from_messages(errors)

            yield cls(
                item=item,
                updated=tuple(updated),
                failed=tuple(failed),
                errors_detail=tuple(errors_detail),
            )

    @classmethod
    def from_batch_create(
            cls, 
            items: Iterable[Item],
            results: Iterable[BatchCreateResult],
    ) -> Iterator[UpdateResult]:
        item_map = {(item.variant_id, item.price): item for item in items}
        
        # group by (variant_id, price)
        def key(result: BatchCreateResult) -> tuple[str, float]:
            return result.listing_input.variant_id, result.listing_input.amount
        
        results = sorted(results, key=key)
        for variant_price, item_results in groupby(results, key=key):
            item = item_map.get(variant_price)

            if not item:
                continue

            created = tuple(result.listing_id for result in item_results)
            errors_detail = tuple(ErrorDetail.from_results(item_results))
            
            yield cls(item, created, errors_detail=errors_detail)

    @classmethod
    def from_batch_delete(
            cls, 
            results: Iterable[BatchDeleteResult],
    ) -> UpdateResult:
        deleted = (result.listing_id for result in results if not result.error)
        failed = (result.listing_input.id for result in results if result.error)
        errors = (ErrorDetail.from_results(results, include_listing_id=True))

        return cls(
            deleted=tuple(deleted), 
            failed=tuple(failed), 
            errors_detail=tuple(errors)
        )


async def update_quantity(
        stockx: StockX, 
        items: Iterable[Item],
) -> Iterator[UpdateResult]:
    decrease = {item for item in items if item.quantity_to_sync() < 0}
    increase = {item for item in items if item.quantity_to_sync() > 0}

    delete_ids = (item.listing_ids[item.quantity_to_sync():] for item in decrease)
    deleted_results = await delete_listings(stockx, chain.from_iterable(delete_ids))

    increased_results = await create_listings(stockx, increase, sync_quantity=True)

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


async def create_listings(
        stockx: StockX,
        items: Iterable[Item], 
        sync_quantity: bool = False
) -> Iterator[UpdateResult]:

    sum_attrs = ('quantity', 'listing_ids') if sync_quantity else ('quantity',)
    grouped_items = group_and_sum(items, ('variant_id', 'price'), sum_attrs)
    
    batch_ids = []

    for item_batch in batched(grouped_items, 500):
        inputs = BatchCreateInput.from_inventory_items(
            items=item_batch, 
            sync_quantity=sync_quantity
        )
        batch_status = await stockx.batch.create_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    results = await _batch_results(batch_ids, create_listings, 60)
    
    return UpdateResult.from_batch_create(items, results)


async def update_listings(
        stockx: StockX,
        items: Iterable[Item]
) -> Iterator[UpdateResult]:
    update_input = BatchUpdateInput.from_inventory_items(items) # add currency
    batch_ids = []
    
    for inputs in batched(update_input, 500):
        batch_status = await stockx.batch.update_listings(inputs)
        batch_ids.append(batch_status.batch_id)

    results = await _batch_results(batch_ids, update_listings, 60)

    return UpdateResult.from_batch_update(items, results)


async def delete_listings(
        stockx: StockX,
        listing_ids: Iterable[str]
) -> UpdateResult:
    
    batch_ids = []
    for listing_batch in batched(listing_ids, 500):
        batch_status = await stockx.batch.delete_listings(listing_batch)
        batch_ids.append(batch_status.batch_id)

    results = await _batch_results(batch_ids, delete_listings, 60)

    return UpdateResult.from_batch_delete(results)


async def _batch_results(stockx, batch_ids, func, timeout):
    b: Batch = stockx.batch
    action_map = {
        create_listings: (b.create_listings_completed, b.create_listings_items),
        update_listings: (b.update_listings_completed, b.update_listings_items),
        delete_listings: (b.delete_listings_completed, b.delete_listings_items),
    }

    batch_completed, get_items = action_map[func]

    try:
        await batch_completed(batch_ids, timeout)
    except BatchTimeOutError:
        pass

    return [
        result for batch_id in batch_ids
        for result in await get_items(batch_id, status='COMPLETED')
    ]