from __future__ import annotations

from collections.abc import Iterable, AsyncIterator, AsyncIterable, Callable
from collections import defaultdict

from .item import Item
from ...models import Listing


ANY = None


class ListedItems:

    __slots__ = '_conditions', '_filters', '_sku_sizes',

    def __init__(self) -> None:
        self._conditions = list()
        self._filters = defaultdict(set)
        self._sku_sizes = defaultdict(set)
    
    async def get(
            self, 
            offset: int = 0,
            limit: int | None = None, 
    ) -> list[Item]:
        items = await Item.from_listings(self._listings())
        return [
            item for item
            in items[offset:limit - offset]
            if all(condition(item) for condition in self._conditions)
        ]

    def include(
            self,
            *,
            variant_ids: Iterable[str] = ANY,
            skus: Iterable[str] = ANY,
            sku: str = ANY,
            sizes: Iterable[str] = ANY,
    ) -> ListedItems:
        
        def add_to(key, values):
            if values:
                self._filters[key].update(values)

        add_to('variant_ids', variant_ids)
        add_to('skus', skus)
        
        if bool(sku) ^ bool(sizes):
            add_to('skus' if sku else 'sizes', [sku] if sku else sizes)

        elif sku and sizes:
            self._sku_sizes[sku].update(sizes)

        return self

    def filter_by(
            self,
            *,
            variant_ids: Iterable[str] = ANY,
            skus: Iterable[str] = ANY,
            sku: str = ANY,
            sizes: Iterable[str] = ANY,
    ) -> ListedItems:
        skus = [sku] if sku else skus

        def apply_filter(key, values):
            if not values:
                return
            if _filter := self._filters[key]: 
                _filter.intersection_update(values)
            else:
                _filter.update(values)

        apply_filter('variant_ids', variant_ids)
        apply_filter('skus', skus)
        apply_filter('sizes', sizes)

        if sizes:
            self._sku_sizes = {
                sku: sizelist.intersection(sizes) for sku, sizelist
                in self._sku_sizes.items() if sku in skus
            }
        else:
            self._sku_sizes = {
                sku: sizelist for sku, sizelist 
                in self._sku_sizes.items() if sku in skus
            }

        return self

    def filter(
            self, 
            condition: Callable[[Item], bool]
    ) -> ListedItems:
        self._conditions.append(condition)
        return self
    
    def _listings(self) -> AsyncIterator[Listing]:
        
        # filter by variant_id if no other filters are applied
        # otherwise retrieve all
        variant_ids = None
        filtered = self._filtered
        if not(self._sku_sizes) and all(
            not(filters)
            for field, filters in self._filters.items() 
            if field != 'variant_ids'
        ):
            variant_ids = self._filters['variant_ids']  
            filtered = lambda x: x

        return filtered(
            listings.get_all_listings(
                variant_ids=variant_ids,
                listing_statuses=['ACTIVE'], 
                # limit=limit, 
                page_size=100,
            )
        )
    
    def _filtered(
            self, 
            listings: AsyncIterable[Listing],
            /,
    ) -> AsyncIterator[Listing]:
        variant_ids = self._filters['variant_ids']
        skus = self._filters['skus']
        sizes = self._filters['sizes']
        
        def sku_size_check(listing: Listing) -> bool:
            return (
                (listing.variant_value in sizes or not sizes)
                and (listing.sku in skus or not skus)
                or  (listing.variant_value in self._sku_sizes[listing.sku])
            )
        
        def check(listing: Listing) -> bool:
            return (listing.variant_id in variant_ids or not variant_ids)
        
        return (
            listing async for listing in listings
            if check(listing) and sku_size_check(listing)
        )


def get_items():
    return ListedItems()