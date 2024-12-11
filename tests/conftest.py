from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

import stockx
from stockx.ext.inventory import Item, UpdateResult


class MockCatalog:
    async def search_catalog(
            self, 
            query: str, 
            limit: int | None = None, 
            page_size: int = 10
    ) -> AsyncIterator[stockx.Product]:
        yield MagicMock(
            spec=stockx.Product, 
            id='product-id', 
            product_id='product-id', 
            url_key='adidas-yeezy-foam-rnnr-onyx',
            style_id='1203A342-500',
            product_type='sneakers',
            brand='yeezy',
            title='Yeezy Foam RNNR Onyx',
        )       
        
    async def get_all_product_variants(
            self, 
            product_id: str
    ) -> list[stockx.Variant]:
        variant = MagicMock(
            spec=stockx.Variant, 
            variant_id='variant-id', 
            product_id=product_id
        )
        return [variant]
    
    async def get_product_market_data(
            self,
            product_id: str,
            currency: stockx.Currency
    ) -> list[stockx.MarketData]:
        return [
            MagicMock(
                spec=stockx.MarketData,
                variant_id='variant-id',
                currency_code=currency,
                lowest_ask_amount=100.0,
                highest_bid_amount=90.0,
                earn_more_amount=95.0,
                sell_faster_amount=92.0,
                flex_lowest_ask_amount=110.0,
            )
        ]


class MockListings:
    def __init__(self):
        self.mock_listing = None
        self.listings = {}
        self.delete_listing = AsyncMock(
            return_value=MagicMock(spec=stockx.Operation)
        )

    async def create_listing(
            self,
            amount: float,
            variant_id: str,
            currency: stockx.Currency,
            active: bool,
            *args, 
            **kwargs,
    ) -> stockx.Operation:
        listing_id = f'listing-{len(self.listings)}'
        self.mock_listing = MagicMock(
            spec=stockx.ListingDetail,
            listing_id=listing_id,
            amount=amount,
            currency_code=currency,
            active=active,
            payout=MagicMock(
                transaction_fee=0.07,  # 7%
                payment_fee=0.03,      # 3%
            )
        )
        self.listings[listing_id] = self.mock_listing
        return MagicMock(spec=stockx.Operation, listing_id=listing_id)
    
    async def operation_succeeded(self, operation: stockx.Operation) -> bool:
        return True
        
    async def get_listing(self, listing_id: str) -> stockx.ListingDetail:
        return self.listings.get(listing_id, self.mock_listing)
    
    async def get_all_listings(
            self,
            listing_statuses: list[str] | None = None,
            limit: int | None = None,
            page_size: int = 10
    ) -> AsyncIterator[stockx.Listing]:
        for listing in self.listings.values():
            if not listing_statuses or listing.status in listing_statuses:
                yield listing


class MockStockX:
    def __init__(self):
        self.catalog = MockCatalog()
        self.listings = MockListings()
        self.batch = MagicMock()


@pytest.fixture
def mock_stockx():
    return MockStockX()


@pytest.fixture
def item():
    return Item(
        product_id='product-id',
        variant_id='variant-id',
        quantity=2,
        price=100.0,
    )

@pytest.fixture
def mock_publish_listings():
    async def mock_publish_listings(stockx, items):
        return [
            UpdateResult(item, created=['new-listing-id-1', 'new-listing-id-2'])
            for item in items
        ]
    
    return mock_publish_listings


@pytest.fixture
def mock_update_listings():
    async def mock_update_listings(stockx, items):
        return [
            UpdateResult(item, updated=['listing-id-1', 'listing-id-2'])
            for item in items
        ]
    return mock_update_listings

