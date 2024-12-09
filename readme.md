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

### Additional Tools

- `mock_listing` - Create temporary listings for testing
- `search` - Product search utilities

### stockx.ext.inventory

The `Inventory` class provides a high-level interface for managing listings on StockX.
It optimizes performance by batching multiple updates together into single API calls. 
When used as an async context manager, it automatically fetches current selling fees 
and handles pending price and quantity changes on exit.

Features:
- Sell or de-list items in bulk
- Set prices based on market data and custom conditions
- Update item quantities and prices

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
