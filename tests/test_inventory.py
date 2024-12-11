from unittest.mock import AsyncMock, MagicMock

import pytest

import stockx
from stockx.errors import StockXIncompleteOperation
from stockx.ext.inventory import (
    Inventory,  
    ListedItem, 
    MarketValue,
)


@pytest.mark.asyncio
async def test_inventory_context_manager(mock_stockx, monkeypatch):
    monkeypatch.setattr(Inventory, 'update', AsyncMock())
    async with Inventory(mock_stockx) as inventory:
        assert inventory.transaction_fee > 0
        assert inventory.payment_fee > 0

    Inventory.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_inventory_load_fees(mock_stockx):
    inventory = Inventory(mock_stockx)
    await inventory.load_fees()
    
    assert inventory.transaction_fee == 0.07
    assert inventory.payment_fee == 0.03


@pytest.mark.asyncio
async def test_inventory_load_fees_failed(mock_stockx):
    inventory = Inventory(mock_stockx)
    mock_stockx.listings.get_listing = AsyncMock(
        return_value=MagicMock(spec=stockx.ListingDetail, payout=None)
    )
    
    with pytest.raises(RuntimeError):
        await inventory.load_fees()


@pytest.mark.asyncio
async def test_inventory_default_fees(mock_stockx, monkeypatch):
    monkeypatch.setattr(
        Inventory, 'load_fees', AsyncMock(side_effect=RuntimeError)
    )
    inventory = Inventory(mock_stockx)

    try:
        await inventory.load_fees()
    except RuntimeError:
        pass

    assert inventory.transaction_fee == 0.09
    assert inventory.payment_fee == 0.03


@pytest.mark.asyncio
async def test_inventory_price_quantity_change(
    mock_stockx, 
    item, 
    monkeypatch
):
    monkeypatch.setattr(Inventory, 'register_price_change', MagicMock())
    monkeypatch.setattr(Inventory, 'register_quantity_change', MagicMock())
    async with Inventory(mock_stockx) as inventory:
        listed_item = ListedItem(
            item=item,
            inventory=inventory,
            listing_ids=['listing-id-1', 'listing-id-2'],
        )
        listed_item.quantity += 3
        listed_item.price = 110.0

        inventory.register_price_change.assert_called_with(listed_item)
        inventory.register_quantity_change.assert_called_with(listed_item)


@pytest.mark.asyncio
async def test_inventory_sell(
    mock_stockx, 
    item, 
    mock_publish_listings, 
    monkeypatch
):
    monkeypatch.setattr(
        'stockx.ext.inventory.inventory.publish_listings',
        mock_publish_listings
    )

    async with Inventory(mock_stockx) as inventory:
        listed_items = await inventory.sell([item])
        
        assert len(listed_items) == 1
        listed_item = listed_items[0]
        assert isinstance(listed_item, ListedItem)
        assert listed_item._item is item
        assert listed_item.listing_ids == ['new-listing-id-1', 'new-listing-id-2']


@pytest.mark.asyncio
async def test_inventory_change_price(
    mock_stockx, 
    item, 
    mock_update_listings, 
    monkeypatch
):
    monkeypatch.setattr(
        'stockx.ext.inventory.inventory.update_listings',
        mock_update_listings
    )

    async with Inventory(mock_stockx) as inventory:
        listed_item = ListedItem(
            item=item,
            inventory=inventory,
            listing_ids=['listing-id-1', 'listing-id-2'],
        )
        results = await inventory.change_price(
            [listed_item], 
            new_price=lambda item: item.price * 0.9,
            condition=True
        )

        assert len(results) == 1
        assert results[0].item._item is item
        assert results[0].item.price == 90.0
        assert results[0].updated == ['listing-id-1', 'listing-id-2']


@pytest.mark.asyncio
async def test_inventory_change_price_incomplete(
    mock_stockx,
    item,
    monkeypatch
):
    incomplete_operation = StockXIncompleteOperation(
        'Inventory price updates timed out.',
        partial_results=[],
        timed_out_batch_ids=['batch-id']
    )
    monkeypatch.setattr(
        'stockx.ext.inventory.inventory.update_listings',
        AsyncMock(side_effect=incomplete_operation)
    )

    async with Inventory(mock_stockx) as inventory:
        with pytest.raises(StockXIncompleteOperation) as exc_info:
            listed_item = ListedItem(
                item=item,
                inventory=inventory,
                listing_ids=['listing-id-1', 'listing-id-2'],
            )           
            await inventory.change_price(
                [listed_item], 
                new_price=lambda item: item.price * 0.9,
                condition=True
            )
        
        assert exc_info.value.message == 'Inventory price updates timed out.'
        assert exc_info.value.partial_results == []
        assert exc_info.value.timed_out_batch_ids == ['batch-id']


@pytest.mark.asyncio
async def test_inventory_beat_lowest_ask(mock_stockx, item, mock_update_listings, monkeypatch):
    mock_market_data = MagicMock(lowest_ask=MarketValue(amount=80, payout=70))
    monkeypatch.setattr(
        Inventory, 
        'get_item_market_data', 
        AsyncMock(return_value=mock_market_data)
    )
    monkeypatch.setattr(
        'stockx.ext.inventory.inventory.update_listings',
        mock_update_listings
    )
    async with Inventory(mock_stockx) as inventory:
        listed_item = ListedItem(
            item=item,
            inventory=inventory,
            listing_ids=['listing-id-1', 'listing-id-2'],
        )
        results = await inventory.beat_lowest_ask(
            [listed_item],
            beat_by=lambda item: item.price * 0.1,
            percentage=False,
            condition=True
        )

        assert listed_item.price == 70.0
        assert results[0].item is listed_item
        assert results[0].updated == ['listing-id-1', 'listing-id-2']


def test_inventory_calculate_payout(mock_stockx):
    inventory = Inventory(
        mock_stockx,
        currency=stockx.Currency.EUR,
        shipping_fee=7.0,
        minimum_transaction_fee=5.0,
        transaction_fee_percentage=0.09,
        payment_fee_percentage=0.03
    )
    
    amount = 100.0
    expected_payout = (
        amount 
        - max(amount * 0.09, 5.0)  # transaction fee
        - amount * 0.03  # payment fee
        - 7.0  # shipping fee
    )
    
    assert inventory.calculate_payout(amount) == expected_payout


