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

Main features:

#### Request Handling
- 🔄 Automatic token refresh and session management
- 🚦 Request throttling to prevent rate limits
- 🔁 Automatic retries with exponential backoff for failed requests
- ⚡ Response caching for invariant data (e.g., product details)

#### Error Handling
- Automatic retry for common HTTP errors (408, 429, 500, 502, 503, 504)
- Structured error responses with detailed information
- Custom exceptions for different error scenarios (rate limits, timeouts, etc.)

#### Performance Optimizations
- Response caching for invariant data like product details and variants
- Request throttling to maintain optimal throughput
- Batch operations for bulk listing management

### High-Level Abstractions 

- `Inventory` - Optimized high-level interface for managing listings on StockX
- `Item` / `ListedItem` - Abstraction aggregating multiple equal listings into a single inventory entry

### Additional Tools

- `mock_listing` - Create temporary listings for testing
- `search` - Product search utilities

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

## High-Level Abstractions

### Inventory Management

The `Inventory` class provides optimized listing management by batching operations:
