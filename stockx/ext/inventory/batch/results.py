from __future__ import annotations

from collections.abc import Iterable, Iterator
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import chain, groupby
from typing import TypeAlias

from ..item import Item, ListedItem
from ....models import (
    BatchCreateResult,
    BatchUpdateResult,
    BatchDeleteResult,
)


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
    item: Item | ListedItem | None = None
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
        
        # Group results by item
        grouped_results: defaultdict[ListedItem, list[UpdateResult]] = defaultdict(list)
        for result in chain(*results):
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
            items: Iterable[ListedItem],
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
            items: Iterable[ListedItem],
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

            created = tuple(r.listing_id for r in item_results if r.listing_id)
            failed = tuple(r.error for r in results if r.error)
            errors_detail = tuple(ErrorDetail.from_results(item_results))
            
            yield cls(
                item=item, 
                created=created, 
                failed=failed, 
                errors_detail=errors_detail
            )

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