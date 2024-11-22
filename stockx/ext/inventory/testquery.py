from __future__ import annotations

from collections.abc import Iterable, AsyncIterator, AsyncIterable, Callable
from collections import defaultdict

from .inventory import Inventory
from .item import ListedItem
from ...models import Listing


ANY = None


from typing import TypeVar, Any, Generic


T = TypeVar('T')


class Filter(Generic[T]):
    def __init__(
            self,
            class_: type[T],
            getter: Callable[[T], Any],
            condition: Callable[[Any, set[Any]], bool],
    ) -> None:
        self.class_ = class_
        self.extractor = getter
        self.condition = condition
        self.allowed_values = set()

    def include(self, values: Iterable[Any]) -> None:
        if not values:
            return
        self.allowed_values.update(values)

    def apply(self, values: Iterable[Any]) -> None:
        if not values:
            return
        if self.allowed_values:
            self.allowed_values.intersection_update(values)
        else:
            self.allowed_values.update(values)

    def matches(self, obj: T) -> bool:
        if not self.allowed_values:
            return True
        value = self.extractor(obj)
        return self.condition(value, self.allowed_values)
    
    def empty(self) -> bool:
        return not self.allowed_values
    

def create_filter(
    class_: type[T],
    /,
    getter: Callable[[T], Any],
    condition: Callable[[Any, set[Any]], bool],
) -> Filter[T]:
    return Filter(class_, getter, condition)


class ItemsQuery:

    __slots__ = '_filters', 'inventory'

    def __init__(self, inventory: Inventory) -> None:
        self.inventory = inventory  
        self._filters: dict[str, Filter[Listing]] = {
            "product_ids": Filter(
                Listing,
                extractor=lambda listing: listing.product.id,
                condition=lambda product_id, allowed: product_id in allowed,
            ),
            "variant_ids": Filter(
                Listing,
                extractor=lambda listing: listing.variant_id,
                condition=lambda variant_id, allowed: variant_id in allowed,
            ),
            "style_ids": Filter(
                Listing,
                extractor=lambda listing: listing.style_id.split('/'),
                condition=lambda style_ids, allowed: not set(style_ids).isdisjoint(allowed),
            ),
            "sizes": Filter(
                Listing,
                extractor=lambda listing: listing.variant_value,
                condition=lambda size, allowed: size in allowed,
            ),
        }

    async def get(self) -> list[ListedItem]:
        items = await ListedItem.from_inventory_listings(
            inventory=self.inventory,
            listings=self._listings(),
        )
        return [item for item in items]

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
    
    def _listings(self) -> AsyncIterator[Listing]:
        if all(
            filter_.empty()
            for key, filter_ in self._filters.items()
            if key not in ('variant_ids', 'product_ids')
        ):
            # filter by variant_id and product_id if no other filters are applied
            product_ids = self._filters['product_ids'].allowed_values
            variant_ids = self._filters['variant_ids'].allowed_values
            filtered = lambda x: x
        else:
            # otherwise retrieve all
            product_ids, variant_ids = ANY, ANY
            filtered = self._filtered

        return filtered(
            self.inventory.stockx.listings.get_all_listings(
                product_ids=product_ids,
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
        pass
