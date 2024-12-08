from collections.abc import Callable
from dataclasses import dataclass
from typing import NamedTuple

from ...format import pretty_str    
from ...models import Currency, MarketData


class MarketValue(NamedTuple):
    """
    Represents a market value (i.e. Lowest Ask) with its 
    corresponding payout amount.

    Parameters
    ----------
    amount : `float`
        The market value amount.
    payout : `float`
        The calculated payout amount after fees and shipping costs.
    """
    amount: float
    payout: float
    

@pretty_str
@dataclass(slots=True, frozen=True)
class ItemMarketData:
    """Represents the market data for an Item, including calculated payouts.

    Parameters
    ----------
    currency : `Currency`
        The currency the market data is in.
    lowest_ask : `MarketValue | None`
        The Lowest Ask amont and payout.
    highest_bid : `MarketValue | None`
        The Highest Bid amount and payout.
    earn_more : `MarketValue | None`
        The Earn More amount and payout.
    sell_faster : `MarketValue | None`
        The Sell Faster amount and payout.
    flex_lowest_ask : `MarketValue | None`
        The Flex Lowest Ask amount and payout.
    """
    currency: Currency
    lowest_ask: MarketValue | None = None
    highest_bid: MarketValue | None = None
    earn_more: MarketValue | None = None
    sell_faster: MarketValue | None = None
    flex_lowest_ask: MarketValue | None = None


def create_item_market_data(
        market_data: MarketData, 
        payout_calculator: Callable[[float], float],
) -> ItemMarketData:
    """
    Create an ItemMarketData instance from a variant market data response object.

    Parameters
    ----------
    market_data : `MarketData`
        Raw variant market data object.
    payout_calculator : `Callable[[float], float]`
        Function that calculates the payout for a given amount.
    currency : `Currency`
        The currency for the market data.

    Returns
    -------
    `ItemMarketData`
        A structured representation of market data with calculated payouts.
    """
    
    def market_value(amount):
        if not amount:
            return None
        return MarketValue(amount, payout_calculator(amount))

    return ItemMarketData(
        currency=market_data.currency_code,
        lowest_ask=market_value(market_data.lowest_ask_amount),
        highest_bid=market_value(market_data.highest_bid_amount),
        earn_more=market_value(market_data.earn_more_amount),
        sell_faster=market_value(market_data.sell_faster_amount),
        flex_lowest_ask=market_value(market_data.flex_lowest_ask_amount),
    )
