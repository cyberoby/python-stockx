from dataclasses import dataclass
from typing import NamedTuple, TYPE_CHECKING

from ...models import MarketData

if TYPE_CHECKING:
    from .inventory import Inventory


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


def create_item_market_data(
        market_data: MarketData, 
        inventory: Inventory
) -> ItemMarketData:
    
    def market_value(amount):
        if not amount:
            return None
        return MarketValue(amount, inventory.calculate_payout(amount))
    
    if market_data.currency_code != inventory.currency:
        raise ValueError(
                f'Currency mismatch: {inventory.currency=} '
                f'{market_data.currency_code=}'
            )

    return ItemMarketData(
        currency=inventory.currency,
        lowest_ask=market_value(market_data.lowest_ask_amount),
        highest_bid=market_value(market_data.highest_bid_amount),
        earn_more=market_value(market_data.earn_more_amount),
        sell_faster=market_value(market_data.sell_faster_amount),
        flex_lowest_ask=market_value(market_data.flex_lowest_ask_amount),
    )
