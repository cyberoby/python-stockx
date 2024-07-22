from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from stockx.models.base import StockXBaseModel


@dataclass
class ProductAttributes(StockXBaseModel):
    gender: str = ''
    season: str = ''
    release_date: str = ''
    retail_price: float = 0
    colorway: str = ''
    color: str = ''

    _numeric_fields = (
        'retail_price',
    )
    _datetime_fields = (
        'release_date',
    )


@dataclass
class Product(StockXBaseModel):
    product_id: str
    url_key: str = ''
    style_id: str = ''
    product_type: str = ''
    title: str = ''
    brand: str = ''
    product_attributes: ProductAttributes = None

    _object_fields = (
        ('product_attributes', ProductAttributes),
    )


@dataclass
class ProductShort(StockXBaseModel):
    product_id: str
    product_name: str = ''
    style_id: str = ''


@dataclass
class Variant(StockXBaseModel):
    variant_id: str
    product_id: str
    variant_name: str = ''
    variant_value: str = ''


@dataclass
class VariantShort(StockXBaseModel):
    variant_id: str
    variant_name: str = ''
    variant_value: str = ''    


@dataclass
class MarketData(StockXBaseModel):
    product_id: str
    variant_id: str
    currency_code: str
    lowest_ask_amount: float = 0
    highest_bid_amount: float = 0
    sell_faster_amount: float = 0
    earn_more_amount: float = 0
    
    _numeric_fields = (
        'lowest_ask_amount', 
        'highest_bid_amount',
        'sell_faster_amount',
        'earn_more_amount',
    )


@dataclass
class Shipment(StockXBaseModel):
    tracking_number: str
    ship_by_date: datetime = None
    tracking_url: str = ''
    carrier_code: str = ''
    shipping_label_url: str = ''
    shipping_document_url: str = ''

    _datetime_fields = (
        'ship_by_date',
    )


@dataclass
class AuthenticationDetails(StockXBaseModel):
    status: str = ''
    failure_notes: str = ''


@dataclass
class Adjustments(StockXBaseModel):
    adjustment_type: str = ''
    amount: float = 0
    percentage: float = 0

    _numeric_fields = (
        'amount',
        'percentage',
    )


@dataclass
class Payout(StockXBaseModel):
    total_payout: float
    sale_price: float = 0
    total_adjustments: float = 0
    currency_code: str = ''
    adjustments: list[Adjustments] = field(default_factory=list)

    _numeric_fields = (
        'total_payout',
        'sale_price',
        'total_adjustments',
    )
    _list_fields = (
        ('adjustments', Adjustments),
    )


@dataclass
class Order(StockXBaseModel):
    order_number: str
    listing_id: str
    amount: float
    status: str
    currency_code: str
    variant: VariantShort = None
    product: ProductShort = None
    shipment: Shipment = None
    authentication_details: AuthenticationDetails = None
    payout: Payout = None
    created_at: datetime = None
    updated_at: datetime = None

    _numeric_fields = (
        'amount',
    )
    _datetime_fields = (
        'created_at',
        'updated_at'
    )
    _object_fields = (
        ('variant', VariantShort),
        ('product', ProductShort),
        ('shipment', Shipment),
        ('authentication_details', AuthenticationDetails),
        ('payout', Payout),
    )


@dataclass
class OrderPartial(StockXBaseModel):
    order_number: str
    listing_id: str
    amount: float
    status: str
    currency_code: str
    variant: VariantShort = None
    product: ProductShort = None
    authentication_details: AuthenticationDetails = None
    payout: Payout = None
    created_at: datetime = None
    updated_at: datetime = None

    _numeric_fields = (
        'amount',
    )
    _datetime_fields = (
        'created_at',
        'updated_at'
    )
    _object_fields = (
        ('variant', VariantShort),
        ('product', ProductShort),
        ('authentication_details', AuthenticationDetails),
        ('payout', Payout),
    )


@dataclass
class OrderShort(StockXBaseModel):
    order_number: str
    order_status: str = ''
    order_created_at: datetime = None

    _datetime_fields = (
        'order_created_at',
    )


@dataclass
class Operation(StockXBaseModel):
    listing_id: str
    operation_id: str
    operation_type: str
    operation_status: str
    operation_initiated_by: str = ''
    operation_initiated_via: str = ''
    created_at: datetime = None
    updated_at: datetime = None
        
    _datetime_fields = (
        'created_at',
        'updated_at'
    )


@dataclass
class Listing(StockXBaseModel):
    listing_id: str
    status: str
    amount: float
    currency_code: str
    inventory_type: str = ''
    order: OrderShort = None
    product: ProductShort = None
    variant: VariantShort = None
    authentication_details: AuthenticationDetails = None
    payout: Payout = None
    last_operation: Operation = None
    created_at: datetime = None
    updated_at: datetime = None

    _numeric_fields = (
        'amount',
    )
    _datetime_fields = (
        'created_at',
        'updated_at'
    )
    _object_fields = (
        ('order', OrderShort),
        ('product', ProductShort),
        ('variant', VariantShort),
        ('authentication_details', AuthenticationDetails),
        ('payout', Payout),
        ('last_operation', Operation)
    )


@dataclass
class ListingPartial(StockXBaseModel):
    listing_id: str
    status: str
    amount: float
    currency_code: str
    inventory_type: str = ''
    order: OrderShort = None
    product: ProductShort = None
    variant: VariantShort = None
    authentication_details: AuthenticationDetails = None
    created_at: datetime = None
    updated_at: datetime = None

    _numeric_fields = (
        'amount',
    )
    _datetime_fields = (
        'created_at',
        'updated_at'
    )
    _object_fields = (
        ('order', OrderShort),
        ('product', ProductShort),
        ('variant', VariantShort),
        ('authentication_details', AuthenticationDetails)
    )


@dataclass
class Batch(StockXBaseModel):
    pass