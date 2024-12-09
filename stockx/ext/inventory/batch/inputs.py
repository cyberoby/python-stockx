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
            currency_code=currency.value
        ) for item in grouped_items
    ]
    return batched(inputs, batch_size)


def sync_listings_inputs(
        items: Iterable[ListedItem], 
        currency: Currency, 
        batch_size: int
) -> Iterator[tuple[BatchCreateInput, ...]]:
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
            active=True,
            currency_code=currency.value
        ) for item in grouped_items
    ]
    return batched(inputs, batch_size)


def update_listings_inputs(
        items: Iterable[ListedItem], 
        currency: Currency, 
        batch_size: int
) -> Iterator[tuple[BatchUpdateInput, ...]]:
    inputs = [
        BatchUpdateInput(
            listing_id=listing_id,
            amount=item.price,
            currency_code=currency.value,
            expires_at=datetime(2024, 12, 30),
        )
        for item in items
        for listing_id in item.listing_ids
    ]
    return batched(inputs, batch_size)


def delete_listings_inputs(
        listing_ids: Iterable[str], 
        batch_size: int
) -> Iterator[tuple[str, ...]]:
    return batched(listing_ids, batch_size)
