from __future__ import annotations

from collections.abc import ( 
    AsyncIterable, 
    AsyncIterator, 
    Callable,
    Iterable,
)

from .inventory import Inventory
from .item import ListedItem
from ...filter import Filter
from ...models import Listing


ANY = None


class ItemsQuery:

    __slots__ = '_conditions', '_filters', 'inventory'

    def __init__(self, inventory: Inventory) -> None:
        self.inventory = inventory
        self._filters = {
            'product_ids': Filter(
                Listing, 
                getter=lambda listing: listing.product.id, 
                condition=lambda product_id, allowed: product_id in allowed
            ),
            'variant_ids': Filter(
                Listing, 
                getter=lambda listing: listing.variant.id, 
                condition=lambda variant_id, allowed: variant_id in allowed
            ),
            'style_ids': Filter(
                Listing, 
                getter=lambda listing: listing.style_id.split('/'), 
                condition=lambda style_ids, allowed: not (
                    set(style_ids).isdisjoint(allowed)
                )
            ),
            'sizes': Filter(
                Listing, 
                getter=lambda listing: listing.variant_value, 
                condition=lambda size, allowed: size in allowed
            ),
        }
        self._conditions = list()

    async def get(self) -> list[ListedItem]:
        items = await ListedItem.from_inventory_listings(
            inventory=self.inventory,
            listings=self._listings(),
        )

        return [
            item for item in items
            if all(condition(item) for condition in self._conditions)
        ]
    
    def _listings(self) -> AsyncIterator[Listing]:
        if all(
            _filter.empty()
            for key, _filter in self._filters.items()
            if key not in ('variant_ids', 'product_ids')
        ):
            # filter by variant_id and product_id if no other filters are applied
            product_ids = self._filters['product_ids'].allowed_values
            variant_ids = self._filters['variant_ids'].allowed_values
            filtered = lambda x: x
        else:
            # otherwise retrieve all
            product_ids, variant_ids = None, None
            filtered = self._filtered

        return filtered(
            self.inventory.stockx.listings.get_all_listings(
                product_ids=product_ids,
                variant_ids=variant_ids,
                listing_statuses=['ACTIVE'], 
                page_size=100,
            )
        )
    
    async def _filtered(
            self, 
            listings: AsyncIterable[Listing],
            /,
    ) -> AsyncIterator[Listing]:
        async for listing in listings:
            if all(_filter.match(listing) for _filter in self._filters.values()):
                yield listing

    def filter(
            self, 
            condition: Callable[[ListedItem], bool]
    ) -> ItemsQuery:
        self._conditions.append(condition)
        return self

    def include(
            self,
            *,
            product_ids: Iterable[str] = ANY,
            variant_ids: Iterable[str] = ANY,
            style_ids: Iterable[str] = ANY,
            sizes: Iterable[str] = ANY,
    ) -> ItemsQuery:
        self._filters['product_ids'].include(product_ids)
        self._filters['variant_ids'].include(variant_ids)
        self._filters['style_ids'].include(style_ids)
        self._filters['sizes'].include(sizes)
        return self

    def filter_by(
            self,
            *,
            product_ids: Iterable[str] = ANY,
            variant_ids: Iterable[str] = ANY,
            style_ids: Iterable[str] = ANY,
            sizes: Iterable[str] = ANY,
    ) -> ItemsQuery:
        self._filters['product_ids'].apply(product_ids)
        self._filters['variant_ids'].apply(variant_ids)
        self._filters['style_ids'].apply(style_ids)
        self._filters['sizes'].apply(sizes)
        return self
    

def create_items_query(inventory: Inventory) -> ItemsQuery:
    return ItemsQuery(inventory)
