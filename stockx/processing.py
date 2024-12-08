from collections.abc import Iterable, Iterator
from functools import reduce
from itertools import groupby
from operator import attrgetter
from typing import TypeVar


T = TypeVar('T')


def group_and_sum(
        iterable: Iterable[T], 
        /, 
        group_keys: Iterable[str], 
        sum_attrs: Iterable[str],
) -> Iterator[T]:
    """
    Group items by `group_keys` and sum values of `sum_attrs` within each group.

    Parameters
    ----------
    iterable : `Iterable[T]`
        An iterable of objects to be grouped and summed.
    group_keys : `Iterable[str]`
        Attribute names to group by. Items with matching values for all
        these attributes will be combined.
    sum_attrs : `Iterable[str]`
        Attribute names whose values should be summed within each group.

    Returns
    -------
    `Iterator[T]`
        An iterator yielding one object per group, with summed attributes.

    Examples
    --------
    >>> items = [
    ...     Item(variant_id='123', price=100, quantity=2),
    ...     Item(variant_id='123', price=100, quantity=3),
    ...     Item(variant_id='456', price=200, quantity=1),
    ... ]
    >>> grouped = group_and_sum(
    ...     items,
    ...     group_keys=('variant_id', 'price'),
    ...     sum_attrs=('quantity',)
    ... )
    >>> list(grouped)  # Returns 2 items:
    [
        Item(variant_id='123', price=100, quantity=5),  # 2 + 3 = 5
        Item(variant_id='456', price=200, quantity=1)
    ]
    """
    def reduce_func(accumulated, item):
        for attr in sum_attrs:
            item_attr = getattr(item, attr)
            accumulated_attr = getattr(accumulated, attr)
            setattr(item, attr, accumulated_attr + item_attr)
        return item
    
    iterable = sorted(iterable, key=attrgetter(*group_keys))
    groups = groupby(iterable, key=attrgetter(*group_keys))
    for _, group in groups:
        yield reduce(reduce_func, group)