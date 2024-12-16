"""
This module provides high-level tools for managing listings on StockX
while minimizing the number of API calls.

Amount and Condition
---------------------
Methods that accept `Amount` or `Condition` parameters support both 
static values and dynamic functions that compute values based on the
item. This allows for an easy implementation of user-defined pricing 
strategies by just injecting the function that computes the values and 
the conditions for updating the price.

Amount : `float | Callable[[ListedItem], float] | Callable[[ListedItem], Awaitable[float]]`

    Can be one of:
    - A fixed float value
    - A function that takes a ListedItem and returns a float
    - An async function that takes a ListedItem and returns a float

Condition : `bool | Callable[[ListedItem], bool] | Callable[[ListedItem], Awaitable[bool]]`

    Can be one of:
    - A fixed boolean value
    - A function that takes a ListedItem and returns a boolean
    - An async function that takes a ListedItem and returns a boolean

Examples
--------
Using static values:
>>> await inventory.beat_lowest_ask(
...     items=items,
...     beat_by=5.0,           # Fixed amount
...     condition=True         # Always apply
... )

Using dynamic functions:
>>> await inventory.change_price(
...     items=items,
...     new_price=lambda item: item.price * 0.95, # Apply 5% discount
...     condition=lambda item: item.payout() > 200  # Only if payout > $200
... )

Using async functions:
>>> async def dynamic_beat_by(item: ListedItem) -> float:
...     market_data = await inventory.get_item_market_data(item)
...     lowest_ask = market_data.lowest_ask.amount
...     highest_bid = market_data.highest_bid.amount
...     bid_ask_spread = lowest_ask - highest_bid
...     return bid_ask_spread * 0.01    # Beat by 1.0% of bid-ask spread
...
>>> async def dynamic_condition(item: ListedItem) -> bool:
...     market_data = await inventory.get_item_market_data(item)
...     return item.price > market_data.lowest_ask.amount   # Only if price > lowest ask
...
>>> await inventory.beat_lowest_ask(
...     items=items,
...     beat_by=dynamic_beat_by,      # Dynamic amount based on market
...     condition=dynamic_condition   # Dynamic condition based on market
... )
"""

from .batch.results import ErrorDetail, UpdateResult
from .inventory import Amount, Condition, Inventory
from .item import Item, ListedItem
from .market import ItemMarketData, MarketValue
from .query import ItemsQuery


__all__ = (
    'Amount',
    'Condition',
    'ErrorDetail',
    'Inventory',
    'Item',
    'ItemMarketData',
    'ItemsQuery',
    'ListedItem', 
    'MarketValue',
    'UpdateResult',
)
