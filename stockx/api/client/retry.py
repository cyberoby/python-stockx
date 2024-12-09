import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from ...errors import StockXRequestError


T = TypeVar('T')


class _RetryDecorator:
    """Retry async function calls until successful or max attempts reached."""

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
) -> _RetryDecorator:
    """Create a decorator that retries failed API calls with exponential backoff.
    
    Parameters
    ----------
    max_attempts : `int`
        Maximum number of retry attempts before giving up
    initial_delay : `float`
        Initial delay between retries in seconds
    timeout : `float`
        Maximum total time to spend retrying in seconds
        
    Returns
    -------
    `_RetryDecorator`
        Configured retry decorator
        
    Examples
    --------
    >>> @retry(max_attempts=3, initial_delay=1.0, timeout=30.0)
    ... async def get(self, endpoint: str, params: Params | None = None) -> Response:
    ...     # Failed requests will be retried up to 3 times
    ...     # with exponential backoff starting at 1 second
    ...     # and total retry time limited to 30 seconds
    ...     ...
    """
    return _RetryDecorator(max_attempts, initial_delay, timeout)
