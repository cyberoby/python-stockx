from __future__ import annotations

from collections.abc import ( 
    AsyncIterable, 
    AsyncIterator, 
    Callable,
    Iterable,
)
from typing import TYPE_CHECKING
    
from .item import ListedItem
from ...filter import Filter
from ...models import Listing

if TYPE_CHECKING:
    from .inventory import Inventory


ANY = None


class ItemsQuery:
    """
    A query builder for filtering inventory items.

    Parameters
    ----------
    inventory : `Inventory`
        The inventory instance to query items from.

    Notes
    -----
    Performance considerations:
    - Filtering by `product_ids` / `variant_ids` uses targeted API requests
    - Other filters (`style_ids`, `sizes`) require retrieving all listings
    - Custom filter conditions are always applied in-memory
    - For best performance, prefer `product_ids` / `variant_ids` filters 
      when possible
    """

    __slots__ = '_conditions', '_filters', '_inventory'

    def __init__(self, inventory: Inventory) -> None:
        self._inventory = inventory
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

    async def all(self) -> list[ListedItem]:
        """
        Retrieve all items matching the query filters.

        Returns
        -------
        `list[ListedItem]`
            List of items matching all filter conditions.
        """
        items = await ListedItem.from_inventory_listings(
            inventory=self._inventory,
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
            if key not in ('product_ids', 'variant_ids')
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
            self._inventory.stockx.listings.get_all_listings(
                product_ids=product_ids,
                variant_ids=variant_ids,
                listing_statuses=['ACTIVE', 'INACTIVE'], 
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
        """
        Add a custom filter condition.

        Parameters
        ----------
        condition : `Callable[[ListedItem], bool]`
            Function that takes a `ListedItem` and returns `True` 
            if the item matches the condition or `False` otherwise.

        Returns
        -------
        `ItemsQuery`
            The query instance for method chaining.
        """
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
        """
        Include additional values to existing filters.

        Parameters
        ----------
        product_ids : `Iterable[str]`, optional
            Product IDs to include in filter.
        variant_ids : `Iterable[str]`, optional
            Variant IDs to include in filter.
        style_ids : `Iterable[str]`, optional
            Style IDs to include in filter.
        sizes : `Iterable[str]`, optional
            Sizes to include in filter.

        Returns
        -------
        `ItemsQuery`
            The query instance for method chaining.
        """
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
        """
        Set filter allowed values.

        Parameters
        ----------
        product_ids : `Iterable[str]`, optional
            Product IDs to filter by.
        variant_ids : `Iterable[str]`, optional
            Variant IDs to filter by.
        style_ids : `Iterable[str]`, optional
            Style IDs to filter by.
        sizes : `Iterable[str]`, optional
            Sizes to filter by.

        Returns
        -------
        `ItemsQuery`
            The query instance for method chaining.
        """
        self._filters['product_ids'].apply(product_ids)
        self._filters['variant_ids'].apply(variant_ids)
        self._filters['style_ids'].apply(style_ids)
        self._filters['sizes'].apply(sizes)
        return self
    

def create_items_query(inventory: Inventory) -> ItemsQuery:
    """
    Create a new ItemsQuery instance.

    Parameters
    ----------
    inventory : `Inventory`
        The inventory instance to query items from.

    Returns
    -------
    `ItemsQuery`
        A new query builder instance.
    """
    return ItemsQuery(inventory)
