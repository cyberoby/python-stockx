import asyncio

import pytest

from stockx.cache import cache_by


@pytest.mark.asyncio
async def test_cache_decorator() -> None:
    calls = 0

    @cache_by('param1', 'param2', maxsize=2, ttl=1.0)
    async def cached_func(param1: str, param2: int) -> tuple[str, int]:
        nonlocal calls
        calls += 1
        return param1, param2

    result1 = await cached_func('test', 123)
    assert result1 == ('test', 123)
    assert calls == 1, 'First call should hit the function'
    
    result2 = await cached_func('test', 123)
    assert result2 == ('test', 123)
    assert calls == 1, 'Second call with same params should use cache'
    
    result3 = await cached_func('test2', 456)
    assert result3 == ('test2', 456)
    assert calls == 2, 'Different params should hit function again'

    result4 = await cached_func('test3', 789)
    assert result4 == ('test3', 789)
    assert calls == 3, 'Different params should hit function again'

    result5 = await cached_func('test', 123)
    assert result5 == ('test', 123)
    assert calls == 4, 'Oldest item should be removed when max size is reached'

    await asyncio.sleep(1.1)
    result6 = await cached_func('test', 123)
    assert result6 == ('test', 123)
    assert calls == 5, 'Cache should be expired after ttl'

