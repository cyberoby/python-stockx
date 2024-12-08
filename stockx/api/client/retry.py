import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from ...exceptions import StockXRequestError


T = TypeVar('T')


class _Retry:

    def __init__(
            self,
            max_attempts: int,
            initial_delay: float,
            timeout: float,
    ) -> None:
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.timeout = timeout
        self.status_codes = {408, 429, 500, 502, 503, 504}

    def __call__(
            self,
            func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            waited = 0
            for attempt in range(self.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except StockXRequestError as e:
                    last_error = e

                    if e.status_code not in self.status_codes:
                        break
                    if waited >= self.timeout:
                        break
                    
                    sleep = min(self.delay(attempt), self.timeout - waited)
                    await asyncio.sleep(sleep)
                    waited += sleep
            raise last_error
        return wrapper

    def delay(self, attempt: int) -> float:
        delay = self.initial_delay * (2 ** attempt)
        # Random jitter of max 10% of delay
        jitter = delay * 0.1 * (asyncio.get_event_loop().time() % 1.0)
        return delay + jitter


def retry(
        max_attempts: int = 6,
        initial_delay: float = 1.0,
        timeout: float = 60.0,
) -> _Retry:
    return _Retry(max_attempts, initial_delay, timeout)
