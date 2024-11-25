from collections.abc import Callable
from dataclasses import dataclass, fields
from typing import NamedTuple

from ...models import MarketData


class MarketValue(NamedTuple):
    amount: float
    payout: float
    

@dataclass(slots=True, frozen=True)
class ItemMarketData:
    currency: str
    lowest_ask: MarketValue | None = None
    highest_bid: MarketValue | None = None
    earn_more: MarketValue | None = None
    sell_faster: MarketValue | None = None
    flex_lowest_ask: MarketValue | None = None

    def __str__(self) -> str:
        indent = '  '
        class_name = self.__class__.__name__

        attributes = '\n'.join(
            f'{indent}  {field.name}: {getattr(self, field.name)}'
            for field in fields(self)
        )

        return f'{class_name}:\n{attributes}'


def create_item_market_data(
        market_data: MarketData, 
        payout_calculator: Callable[[float], float],
        currency: str,
) -> ItemMarketData:
    
    def market_value(amount):
        if not amount:
            return None
        return MarketValue(amount, payout_calculator(amount))
    
    if market_data.currency_code != currency:
        raise ValueError(
                f'Currency mismatch: {currency=} '
                f'{market_data.currency_code=}'
            )

    return ItemMarketData(
        currency=currency,
        lowest_ask=market_value(market_data.lowest_ask_amount),
        highest_bid=market_value(market_data.highest_bid_amount),
        earn_more=market_value(market_data.earn_more_amount),
        sell_faster=market_value(market_data.sell_faster_amount),
        flex_lowest_ask=market_value(market_data.flex_lowest_ask_amount),
    )
