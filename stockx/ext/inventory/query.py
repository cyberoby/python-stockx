from __future__ import annotations

from collections.abc import Iterable, AsyncIterator, AsyncIterable, Callable
from collections import defaultdict

from .inventory import Inventory
from .item import ListedItem
from ...models import Listing


ANY = None


class ItemsQuery:

    __slots__ = '_conditions', '_filters', '_limit', '_offset', '_sku_sizes'

    def __init__(self, inventory: Inventory) -> None:
        self.inventory = inventory  
        self._conditions = list()
        self._filters = defaultdict(set)
        self._sku_sizes = defaultdict(set)
        self._limit = 0
        self._offset = 0
    
    async def get(self) -> list[ListedItem]:
        items = await ListedItem.from_inventory_listings(
            inventory=self.inventory,
            listings=self._listings(),
        )
        return [
            item for item
            in items[self._offset:self._limit + self._offset]
            if all(condition(item) for condition in self._conditions)
        ]

    def offset(self, n: int, /) -> ItemsQuery:
        self._offset = n
        return self

    def limit(self, n: int, /) -> ItemsQuery:
        self._limit = n
        return self

    def include(
            self,
            *,
            variant_ids: Iterable[str] = ANY,
            skus: Iterable[str] = ANY,
            sku: str = ANY,
            sizes: Iterable[str] = ANY,
    ) -> ItemsQuery:
        
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
    ) -> ItemsQuery:
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
            condition: Callable[[ListedItem], bool]
    ) -> ItemsQuery:
        self._conditions.append(condition)
        return self
    
    def _listings(self) -> AsyncIterator[Listing]:
        if not(self._sku_sizes) and all(
            not(filters)
            for field, filters in self._filters.items() 
            if field != 'variant_ids'
        ):
            # filter by variant_id if no other filters are applied
            variant_ids = self._filters['variant_ids']  
            filtered = lambda x: x
        else:
            # otherwise retrieve all
            variant_ids = None
            filtered = self._filtered

        return filtered(
            self.inventory.stockx.listings.get_all_listings(
                variant_ids=variant_ids,
                listing_statuses=['ACTIVE'], 
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
            return listing.variant_value in self._sku_sizes[listing.style_id]
        
        def variant_id_check(listing: Listing) -> bool:
            return listing.variant.id in variant_ids or not variant_ids
        
        def style_id_check(listing: Listing) -> bool:
            return not (set(listing.style_id.split('/')).isdisjoint(skus) and skus)
        
        def size_check(listing: Listing) -> bool:
            return (listing.variant_value in sizes or not sizes)
        
        return (
            listing async for listing in listings if
            variant_id_check(listing) 
            and style_id_check(listing)
            and size_check(listing)
            and sku_size_check(listing)
        )
    
