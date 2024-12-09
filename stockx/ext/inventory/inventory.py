from __future__ import annotations
from collections.abc import (
    Callable,
    Iterable, 
    Iterator,
)
from typing import TYPE_CHECKING

from .batch.operations import (
    publish_listings,
    update_listings, 
    update_quantity,
)
from .batch.results import UpdateResult
from .item import Item, ListedItem
from .market import create_item_market_data
from .query import create_items_query
from ..mock import mock_listing
from ...api import StockX
from ...models import Currency
from ...types import ComputedValue, computed_value

if TYPE_CHECKING:
    from .market import ItemMarketData, MarketValue
    from .query import ItemsQuery


Amount = ComputedValue[ListedItem, float]
Condition = ComputedValue[ListedItem, bool]


class Inventory:
    """
    Provides a high-level interface for managing listings on StockX.

    This class optimizes performance by batching multiple updates together into
    single API calls. When used as an async context manager, it automatically
    fetches current selling fees and handles pending price and quantity changes
    on exit.

    Features:
    - Sell or de-list items in bulk
    - Set prices based on market data and custom conditions
    - Update item quantities and prices

    Parameters
    ----------
    stockx : `StockX`
        The StockX API interface instance.
    currency : `Currency`, default EUR
        The currency to use for prices.
    shipping_fee : `float`, default 7.0
        Shipping fee per item.
    minimum_transaction_fee : `float`, default 5.0
        Minimum transaction fee per sale.
    transaction_fee_percentage : `float`, default 9.0%
        Current selling fee.
    payment_fee_percentage : `float`, default 3.0%
        Current payment processing fee.

    Examples
    --------
    >>> client = StockXAPIClient(...)
    >>> async with StockX(client) as stockx:
    ...     async with Inventory(stockx) as inventory:
    ...         # Get items listed for over 200 payout
    ...         items = await (
    ...             inventory.items()
    ...             .filter(lambda item: item.payout() > 200)
    ...             .all()
    ...         )
    ...         for item in items:
    ...             item.price -= 20    # Reduce price by 20
    ...             item.quantity += 1  # Increase quantity by 1 
    ...         # Changes are automatically applied when exiting context
    """

    __slots__ = (
        '_price_updates',
        '_quantity_updates',
        'currency',
        'minimum_transaction_fee',
        'payment_fee',
        'shipping_fee',
        'stockx',
        'transaction_fee',
    )

    def __init__(
            self, 
            stockx: StockX, 
            currency: Currency = Currency.EUR,
            shipping_fee: float = 7.0,
            minimum_transaction_fee: float = 5.0,
            transaction_fee_percentage: float = 0.09,
            payment_fee_percentage: float = 0.03
    ) -> None:
        self.stockx = stockx
        self.currency = currency
        self.shipping_fee = shipping_fee
        self.minimum_transaction_fee = minimum_transaction_fee
        self.transaction_fee = transaction_fee_percentage
        self.payment_fee = payment_fee_percentage

        self._price_updates: set[ListedItem] = set()
        self._quantity_updates: set[ListedItem] = set()

    async def __aenter__(self) -> Inventory:
        await self.load()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        results = await self.update()
        # TODO: return True and suppress exc?

    async def load(self) -> None:
        """Load inventory configuration like fees from StockX."""
        await self.load_fees()

    async def load_fees(self) -> None:
        """
        Load current StockX selling fees.
        
        Raises
        ------
        `RuntimeError`
            If unable to load fees. Default fees applied.
        """
        async for listing in self.stockx.listings.get_all_listings(
            listing_statuses=['ACTIVE'],
            limit=100,
            page_size=100,
        ):
            detail = await self.stockx.listings.get_listing(listing.id)
            if detail.payout:
                self.transaction_fee = detail.payout.transaction_fee
                self.payment_fee = detail.payout.payment_fee
                return
        
        async with mock_listing(
            stockx=self.stockx, 
            currency=self.currency
        ) as detail:
            if detail and detail.payout:
                self.transaction_fee = detail.payout.transaction_fee
                self.payment_fee = detail.payout.payment_fee
                return
        
        raise RuntimeError('Unable to load fees. Default fees applied.')
    
    def items(self) -> ItemsQuery:
        """
        Create a query builder for retrieving and filtering inventory items.

        Examples
        --------
        >>> async with Inventory(stockx) as inventory:
        ...     # Get all items with style ID 'L47450600'
        ...     salomons_gtx = await inventory.items().filter_by(style_ids=['L47450600']).all()
        ...   
        ...     print(salomons_gtx[0].style_id)
        ...     print(salomons_gtx[0].name)
        ...     print(salomons_gtx[0].size)
        ...     print(f'${salomons_gtx[0].payout():.2f}')
        ...     print(salomons_gtx[0].quantity)
        ...    
        L47450600
        Salomon XT-6 Gore-Tex Black Silver
        11.5
        $167.40
        3
        """
        return create_items_query(self)
    
    async def get_item_market_data(
            self, 
            item: Item | ListedItem
    ) -> ItemMarketData:
        market_data = await self.stockx.catalog.get_product_market_data(
            product_id=item.product_id, 
            currency=self.currency
        )

        variant_market_data = next(
            data for data in market_data 
            if data.variant_id == item.variant_id
        )
        
        return create_item_market_data(
            market_data=variant_market_data, 
            payout_calculator=self.calculate_payout, 
        )
    
    def calculate_payout(self, amount: float) -> float:
        """
        Calculate the net payout for a given listing (or Ask) amount.

        Parameters
        ----------
        amount : `float`
            The Listing (or Ask) amount.

        Returns
        -------
        `float`
            Payout after deducting transaction fees, payment fees,
            and shipping costs.
        """
        transaction_fee = max(
            self.transaction_fee * amount,  
            self.minimum_transaction_fee
        )
        return (
            amount 
            - transaction_fee 
            - self.payment_fee * amount 
            - self.shipping_fee
        )
    
    def register_price_change(self, item: ListedItem) -> None:
        self._price_updates.add(item)

    def register_quantity_change(self, item: ListedItem) -> None:
        self._quantity_updates.add(item)

    async def update(self) -> Iterator[UpdateResult]:
        """Apply all pending price and quantity changes."""
        quantity_results, price_results = [], []

        if self._quantity_updates:
            quantity_results = await update_quantity(
                stockx=self.stockx, 
                items=self._quantity_updates
            )
        if self._price_updates:
            print('price')
            price_results = await update_listings(
                stockx=self.stockx, 
                items=self._price_updates
            )

        self._price_updates.clear()
        self._quantity_updates.clear()

        return UpdateResult.consolidate(quantity_results, price_results)
    
    async def sell(self, items: Iterable[Item]) -> list[ListedItem]:
        """
        Create new listings for the provided items.

        Parameters
        ----------
        items : `Iterable[Item]`
            Items to sell.

        Returns
        -------
        `list[ListedItem]`
            Collection of items successfully listed.

        Examples
        --------
        >>> client = StockXAPIClient(...)
        >>> async with StockX(client) as stockx:
        ...     async with Inventory(stockx) as inventory:
        ...         # Create items from SKU and size (Air Force 1 '07 Triple White)
        ...         af1_size_9 = await Item.from_sku_size(stockx, 'CW2288-111', 'US 9', 110.00)  
        ...         af1_size_85 = await Item.from_sku_size(stockx, 'CW2288-111', 'US 8.5', 110.00)
        ...         
        ...         # Create listings
        ...         listed_items = await inventory.sell([af1_size_9, af1_size_85])
        ...         
        ...         # Print results
        ...         for item in listed_items:
        ...             print(f'Expected payout: ${item.payout()}')
        ... 
        Expected payout: $89.80
        Expected payout: $89.80
        """
        results = await publish_listings(self.stockx, items)
        return [
            ListedItem(
                item=result.item, 
                inventory=self, 
                listing_ids=result.created
            )
            for result in results
            if result.created
        ]
    
    async def change_price(
            self,
            items: Iterable[ListedItem],
            new_price: Amount,
            condition: Condition = True,
    ) -> Iterator[UpdateResult]:
        """
        Update prices for items that meet the given condition.

        Parameters
        ----------
        items : `Iterable[ListedItem]`
            Items to update prices for.
        new_price : `Amount`
            New price to set. See module docs for details.
        condition : `Condition`, optional
            Condition that must be met to update price. See module docs for details.

        Returns
        -------
        `Iterator[UpdateResult]`
            Results of the price updates.

        Examples
        --------
        >>> # Apply 10% discount to items with payout over 200
        >>> await inventory.change_price(
        ...     items=items,
        ...     new_price=lambda item: item.price * 0.9,
        ...     condition=lambda item: item.payout() > 200
        ... )
        """
        items_to_update = []

        for item in items: 
            if await computed_value(item, condition):
                # Change item's price if condition is met
                new_price = await computed_value(item, new_price)
                if new_price != item.price: # Avoid unnecessary updates
                    item.price = new_price
                    items_to_update.append(item)

        # Avoid unnecessary updates when calling Inventory.update()
        self._price_updates.difference_update(items_to_update)

        # Sync changes to StockX
        return await update_listings(self.stockx, items_to_update)
    
    async def _beat_market_value(
            self,
            items: Iterable[ListedItem], 
            get_market_value: Callable[[ItemMarketData], MarketValue | None],
            beat_by: Amount,
            percentage: bool,
            condition: Condition,
    ) -> Iterator[UpdateResult]:
        # Define a new price function depending on market data
        async def new_price(item: ListedItem) -> float:
            change = await computed_value(item, beat_by)
            
            market_data = await self.get_item_market_data(item)
            market_value = get_market_value(market_data)

            if not market_value:
                return item.price # Keep current price

            if percentage:  
                return market_value.amount * (1 - change)
            else:
                return market_value.amount - change
            
        return await self.change_price(items, new_price, condition)

    async def beat_lowest_ask(
            self,
            items: Iterable[ListedItem], 
            beat_by: Amount = 1,
            percentage: bool = False,
            condition: Condition = True,
    ) -> Iterator[UpdateResult]:
        """
        Beat the Lowest Ask by a given amount and if condition is met.

        Parameters
        ----------
        items : `Iterable[ListedItem]`
            Items to update the listing amount for.
        beat_by : `Amount`, default 1
            Amount to beat lowest ask by. Can be a fixed value, function,
            or async function. See module docs for details.
        percentage : `bool`, default False
            If `True`, beat_by is treated as percentage on the listing amount.
        condition : `Condition`, default True
            Condition that must be met to beat the lowest ask. 
            Can be a fixed value, function, or async function.
            See module docs for details.

        Returns
        -------
        `Iterator[UpdateResult]`
            Results of the price updates.
        """
        return await self._beat_market_value(
            items=items, 
            get_market_value=lambda m: m.lowest_ask, 
            beat_by=beat_by, 
            condition=condition, 
            percentage=percentage
        )

    async def beat_sell_faster(
            self,
            items: Iterable[ListedItem], 
            beat_by: Amount = 0,
            percentage: bool = False,
            condition: Condition = True,
    ) -> Iterator[UpdateResult]:
        """
        Like `beat_lowest_ask`, but targets StockX's "Sell Faster" price suggestion.
        See `beat_lowest_ask` for parameter details.
        """
        return await self._beat_market_value(
            items=items, 
            get_market_value=lambda m: m.sell_faster, 
            beat_by=beat_by, 
            condition=condition, 
            percentage=percentage
        )

    async def beat_earn_more(
            self,
            items: Iterable[ListedItem], 
            beat_by: Amount = 0,
            percentage: bool = False,
            condition: Condition = True,
    ) -> Iterator[UpdateResult]:
        """
        Like `beat_lowest_ask`, but targets StockX's "Earn More" price suggestion.
        See `beat_lowest_ask` for parameter details.
        """
        return await self._beat_market_value(
            items=items, 
            get_market_value=lambda m: m.earn_more, 
            beat_by=beat_by, 
            condition=condition, 
            percentage=percentage
        )
        
    

    

