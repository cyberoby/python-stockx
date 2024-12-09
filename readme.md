# StockX Python SDK

An async Python SDK for interacting with the StockX API, providing both low-level endpoint mappings and high-level inventory management abstractions.

> ⚠️ This SDK is under active development

The SDK has two layers: 
- `stockx`: low-level API client for easy access to StockX API endpoints
- `stockx.ext`: high-level abstractions for advanced business logic

## stockx
Direct mappings to StockX API endpoints through specialized interfaces:

- `Catalog` - Product catalog operations
- `Listings` - Listing management 
- `Orders` - Sales order operations
- `Batch` - Batch listing operations

#### Main features
- 🔄 Automatic token refresh and session management
- 🚦 Request throttling to prevent rate limits
- 🔁 Automatic retries with exponential backoff for failed requests
- ⚡ Response caching for invariant data (e.g., product details)

## stockx.ext

High-level abstractions for advanced business logic and inventory management:

- `Inventory` - Optimized high-level interface for managing listings on StockX
- `Item` / `ListedItem` - Abstraction aggregating multiple equal listings into a single inventory entry
- `mock_listing` - Create temporary listings for testing
- `search` - Product search utilities

### stockx.ext.inventory.Inventory

The `Inventory` class provides a high-level interface for managing listings on StockX.
It optimizes performance by batching multiple updates together into single API calls. 

Features:
- Sell or de-list items in bulk
- Set prices based on market data and custom conditions
- Update item quantities and prices on context exit

### Examples

#### Update item prices and quantities easily

```python
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
```

#### Retrieve listed items by custom criteria

```python
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
```

#### Sell items

```python
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
```

#### Change prices dynamically by injecting user-defined functions
Using functions:
```python
>>> # Apply 10% discount to items with payout over 200
>>> await inventory.change_price(
...     items=items,
...     new_price=lambda item: item.price * 0.9,
...     condition=lambda item: item.payout() > 200
... )
```
Using async functions:
```python
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
```

## API Endpoint Mappings

| Method | Endpoint | SDK Function |
|--------|----------|--------------|
| GET | `/catalog/products/{id}` | `Catalog.get_product()` |
| GET | `/catalog/products/{id}/variants` | `Catalog.get_all_product_variants()` |
| GET | `/catalog/products/{id}/variants/{id}` | `Catalog.get_product_variant()` |
| GET | `/catalog/products/{id}/variants/{id}/market-data` | `Catalog.get_variant_market_data()` |
| GET | `/catalog/products/{id}/market-data` | `Catalog.get_product_market_data()` |
| GET | `/catalog/search` | `Catalog.search_catalog()` |
| GET | `/selling/listings/{id}` | `Listings.get_listing()` |
| GET | `/selling/listings` | `Listings.get_all_listings()` |
| POST | `/selling/listings` | `Listings.create_listing()` |
| DELETE | `/selling/listings/{id}` | `Listings.delete_listing()` |
| PUT | `/selling/listings/{id}/activate` | `Listings.activate_listing()` |
| PUT | `/selling/listings/{id}/deactivate` | `Listings.deactivate_listing()` |
| PATCH | `/selling/listings/{id}` | `Listings.update_listing()` |
| GET | `/selling/listings/{id}/operations/{id}` | `Listings.get_listing_operation()` |
| GET | `/selling/listings/{id}/operations` | `Listings.get_all_listing_operations()` |
| POST | `/selling/batch/create-listing` | `Batch.create_listings()` |
| GET | `/selling/batch/create-listing/{id}` | `Batch.create_listings_status()` |
| GET | `/selling/batch/create-listing/{id}/items` | `Batch.create_listings_items()` |
| POST | `/selling/batch/update-listing` | `Batch.update_listings()` |
| GET | `/selling/batch/update-listing/{id}` | `Batch.update_listings_status()` |
| GET | `/selling/batch/update-listing/{id}/items` | `Batch.update_listings_items()` |
| POST | `/selling/batch/delete-listing` | `Batch.delete_listings()` |
| GET | `/selling/batch/delete-listing/{id}` | `Batch.delete_listings_status()` |
| GET | `/selling/batch/delete-listing/{id}/items` | `Batch.delete_listings_items()` |
| GET | `/selling/orders/{id}` | `Orders.get_order()` |
| GET | `/selling/orders/history` | `Orders.get_orders_history()` |
| GET | `/selling/orders/active` | `Orders.get_active_orders()` |
