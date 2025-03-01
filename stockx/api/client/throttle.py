import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar


T = TypeVar('T')


class _ThrottleDecorator:
    """Throttle async function calls to avoid rate limiting."""
    
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self._queue: deque[tuple[asyncio.Future[T], Awaitable[T]]] = deque()
        self._task: asyncio.Task | None = None
        self._last_request_time = 0.0
    
    async def _requester(self) -> None:
        while True:
            sleep = max(0, self.seconds - (now() - self._last_request_time))
            await asyncio.sleep(sleep)

            if not self._queue:
                continue
            
            self._last_request_time = now()
            future, request = self._queue.popleft()
            try:
                result = await request
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

    def __call__(
            self, 
            func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            loop = asyncio.get_running_loop()
            
            if not self._task:
                self._task = loop.create_task(self._requester())
            
            future = loop.create_future()
            request = func(*args, **kwargs)
            self._queue.append((future, request))
            return await future
        return wrapper
    

def throttle(seconds: float) -> _ThrottleDecorator:
    """Create a decorator that throttles API calls.
    
    Parameters
    ----------
    seconds : `float`
        Minimum time between API calls in seconds
        
    Returns
    -------
    `_Throttler`
        Configured throttling decorator
        
    Examples
    --------
    >>> @throttle(seconds=3)
    ... async def get(self, endpoint: str, params: Params | None = None) -> Response:
    ...     # Requests will be queued and performed every 3 seconds
    ...     ...
    """
    return _ThrottleDecorator(seconds)


def now() -> float:
    return time.time()

