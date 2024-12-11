from unittest.mock import AsyncMock

import pytest

import stockx
from stockx.ext import mock_listing


@pytest.mark.asyncio
async def test_mock_listing_creation(mock_stockx):
    async with mock_listing(
        stockx=mock_stockx, 
        amount=1500, 
        currency=stockx.Currency.JPY
    ) as listing:
        assert listing.amount == 1500
        assert listing.currency_code == stockx.Currency.JPY
        listing_id = listing.listing_id

    mock_stockx.listings.delete_listing.assert_awaited_once_with(listing_id)


@pytest.mark.asyncio
async def test_mock_listing_creation_failed(mock_stockx):
    mock_stockx.listings.operation_succeeded = AsyncMock(return_value=False)
    
    with pytest.raises(RuntimeError):
        async with mock_listing(
            stockx=mock_stockx, 
            amount=1500, 
            currency=stockx.Currency.JPY
        ):
            pass
