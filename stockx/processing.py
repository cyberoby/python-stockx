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