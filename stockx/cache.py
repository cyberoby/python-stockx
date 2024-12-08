import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from functools import wraps
from inspect import signature
from typing import Any, TypeVar


T = TypeVar('T')
Cache = OrderedDict[tuple[Any, ...], tuple[T, float]]


class _CacheDecorator:
    """Cache async function results based on specified parameter values."""

    def __init__(
            self, 
            *cache_keys: str, 
            maxsize: int = 4096,
            ttl: float | None = None,
    ) -> None:
        self.cache_keys = cache_keys
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: Cache[T] = OrderedDict()

    def __call__(
            self,
            func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        sig = signature(func)

        def make_key(*args, **kwargs):
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            return tuple(bound_args.arguments[key] for key in self.cache_keys)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_key(*args, **kwargs)
            now = time.time()
            
            cached_value, timestamp = self._cache.get(key, (None, None))
            if cached_value and (not self.ttl or now - timestamp <= self.ttl):
                return cached_value

            value = await func(*args, **kwargs)
            self._cache[key] = (value, now)
            if len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)
            return value
        return wrapper


def cache_by(
        *cache_keys: str, 
        maxsize: int = 4096, 
        ttl: float | None = None
) -> _CacheDecorator:
    """Create a decorator that caches results based on parameter values.
    
    Parameters
    ----------
    cache_keys : str
        Names of parameters to use as cache keys
    maxsize : `int`
        Maximum number of items to store in the cache
    ttl : `float` | `None`
        Time to live in seconds for cached values. 
        If `None`, cache never expires.
        
    Returns
    -------
    `_CacheDecorator`
        Configured caching decorator
        
    Examples
    --------
    >>> @cache_by('sku', maxsize=4096, ttl=60)
    >>> async def get_product_market_data(
    ...     self, 
    ...     product_id: str, 
    ...     currency_code: str
    ... ) -> list[MarketData]:
    ...     # Results will be cached based on the sku parameter
    ...     # Cached results will expire after ttl seconds
    ...     ...
    """
    return _CacheDecorator(*cache_keys, maxsize=maxsize, ttl=ttl)