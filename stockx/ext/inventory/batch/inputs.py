from collections.abc import Iterable, Iterator
from datetime import datetime
from itertools import batched

from ..item import Item, ListedItem
from ....models import (
    BatchCreateInput, 
    BatchUpdateInput, 
    Currency
)
from ....processing import group_and_sum


def create_listings_inputs(
        items: Iterable[Item], 
        currency: Currency, 
        batch_size: int
) -> Iterator[tuple[BatchCreateInput, ...]]:
    """Create batch input items for creating new listings.

    Groups items by variant ID and price to minimize API calls.
    """
    grouped_items = group_and_sum(
        items, 
        group_keys=('variant_id', 'price'), 
        sum_attrs=('quantity',)
    )
    inputs = [
        BatchCreateInput(
            variant_id=item.variant_id, 
            amount=item.price, 
            quantity=item.quantity,
            active=True,
            currency_code=currency
        ) for item in grouped_items
    ]
    return batched(inputs, batch_size)


def sync_listings_inputs(
        items: Iterable[ListedItem], 
        currency: Currency,
        batch_size: int
) -> Iterator[tuple[BatchCreateInput, ...]]:
    """Create batch input items for syncing listing quantities.

    Groups items by variant ID and price to minimize API calls.
    Uses `ListedItem.quantity_to_sync()` to determine how many 
    listings to create.
    """
    grouped_items = group_and_sum(
        items, 
        group_keys=('variant_id', 'price'), 
        sum_attrs=('quantity', 'listing_ids')
    )
    inputs = [
        BatchCreateInput(
            variant_id=item.variant_id, 
            amount=item.price, 
            quantity=item.quantity_to_sync(),
            currency_code=currency
        ) for item in grouped_items
    ]
    return batched(inputs, batch_size)


def update_listings_inputs(
        items: Iterable[ListedItem], 
        batch_size: int
) -> Iterator[tuple[BatchUpdateInput, ...]]:
    """Create batch input items for updating existing listings."""
    inputs = [
        BatchUpdateInput(
            listing_id=listing_id,
            amount=item.price,
            currency_code=item.currency,
        )
        for item in items
        for listing_id in item.listing_ids
    ]
    return batched(inputs, batch_size)


def delete_listings_inputs(
        listing_ids: Iterable[str], 
        batch_size: int
) -> Iterator[tuple[str, ...]]:
    """Create batched inputs for deleting listings."""
    return batched(listing_ids, batch_size)
