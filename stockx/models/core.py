from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from stockx.models.base import StockXBaseModel


@dataclass(frozen=True, slots=True)
class ProductAttributes(StockXBaseModel):
    gender: str = ''
    season: str = ''
    release_date: str = ''
    retail_price: float | None = None
    colorway: str = ''
    color: str = ''


@dataclass(frozen=True, slots=True)
class Product(StockXBaseModel):
    product_id: str
    url_key: str = ''
    style_id: str = ''
    product_type: str = ''
    title: str = ''
    brand: str = ''
    product_attributes: ProductAttributes | None = None


@dataclass(frozen=True, slots=True)
class ProductShort(StockXBaseModel):
    product_id: str
    product_name: str = ''
    style_id: str = ''


@dataclass(frozen=True, slots=True)
class Variant(StockXBaseModel):
    variant_id: str
    product_id: str
    variant_name: str = ''
    variant_value: str = ''


@dataclass(frozen=True, slots=True)
class VariantShort(StockXBaseModel):
    variant_id: str
    variant_name: str = ''
    variant_value: str = ''    


@dataclass(frozen=True, slots=True)
class MarketData(StockXBaseModel):
    product_id: str
    variant_id: str
    currency_code: str
    lowest_ask_amount: float | None = None
    highest_bid_amount: float | None = None
    sell_faster_amount: float | None = None
    earn_more_amount: float | None = None
    flex_lowest_ask_amount: float | None = None
    

@dataclass(frozen=True, slots=True)
class Shipment(StockXBaseModel):
    tracking_number: str
    ship_by_date: datetime | None = None
    tracking_url: str = ''
    carrier_code: str = ''
    shipping_label_url: str = ''
    shipping_document_url: str = ''


@dataclass(frozen=True, slots=True)
class AuthenticationDetails(StockXBaseModel):
    status: str = ''
    failure_notes: str = ''


@dataclass(frozen=True, slots=True)
class Adjustments(StockXBaseModel):
    adjustment_type: str = ''
    amount: float = 0
    percentage: float = 0


@dataclass(frozen=True, slots=True)
class Payout(StockXBaseModel):
    total_payout: float
    sale_price: float | None = None
    total_adjustments: float = 0
    currency_code: str = ''
    adjustments: list[Adjustments] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Order(StockXBaseModel):
    order_number: str
    listing_id: str
    amount: float
    status: str
    currency_code: str
    product: ProductShort
    variant: VariantShort | None = None
    authentication_details: AuthenticationDetails | None = None
    payout: Payout | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class OrderDetail(Order):
    shipment: Shipment | None = None


@dataclass(frozen=True, slots=True)
class OrderShort(StockXBaseModel):
    order_number: str
    order_status: str = ''
    order_created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Operation(StockXBaseModel):
    listing_id: str
    operation_id: str
    operation_type: str
    operation_status: str
    operation_initiated_by: str = ''
    operation_initiated_via: str = ''
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # TODO: changes, operation_url?


@dataclass(frozen=True, slots=True)
class Listing(StockXBaseModel):
    listing_id: str
    status: str
    amount: float
    currency_code: str
    product: ProductShort
    variant: VariantShort | None = None
    inventory_type: str = ''
    order: OrderShort | None = None
    authentication_details: AuthenticationDetails | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ListingDetail(Listing):
    payout: Payout | None = None
    last_operation: Operation | None = None


@dataclass(frozen=True, slots=True)
class BatchStatus(StockXBaseModel):
    pass