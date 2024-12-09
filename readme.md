# StockX Python SDK

An async Python SDK for interacting with the StockX API, providing both low-level endpoint mappings and high-level inventory management abstractions.

> ⚠️ This SDK is under active development

## Overview

The SDK is structured in layers:

### Low-Level API Client
Direct mappings to StockX API endpoints through specialized interfaces:

- `Catalog` - Product catalog operations
- `Listings` - Listing management 
- `Orders` - Sales order operations
- `Batch` - Batch listing operations

### High-Level Abstractions 

- `Inventory` - Optimized inventory management with batched operations
- `Item`/`ListedItem` - Product variant aggregation for simplified inventory tracking
- `ItemsQuery` - Fluent query builder for filtering inventory items

### Additional Tools

- `mock_listing` - Create temporary listings for testing
- `search` - Product search utilities by SKU and URL

## API Endpoint Mappings

| Endpoint | Method | SDK Function |
|----------|--------|--------------|
| `/catalog/products/{id}` | GET | `stockx.catalog.get_product()` |
| `/catalog/products/{id}/variants/{id}/market-data` | GET | `stockx.catalog.get_variant_market_data()` |
| `/catalog/search` | GET | `stockx.catalog.search_catalog()` |
| `/selling/listings/{id}` | GET | `stockx.listings.get_listing()` |
| `/selling/listings` | POST | `stockx.listings.create_listing()` |
| `/selling/listings/{id}` | DELETE | `stockx.listings.delete_listing()` |
| `/selling/batch/create-listing` | POST | `stockx.batch.create_listings()` |
| `/selling/batch/update-listing` | POST | `stockx.batch.update_listings()` |
| `/selling/batch/delete-listing` | POST | `stockx.batch.delete_listings()` |
| `/selling/orders/{id}` | GET | `stockx.orders.get_order()` |

## High-Level Abstractions

### Inventory Management

The `Inventory` class provides optimized listing management by batching operations:
