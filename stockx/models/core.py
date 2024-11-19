from __future__ import annotations
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TYPE_CHECKING

from .base import StockXBaseModel
from ..format import iso

if TYPE_CHECKING:
    from ..ext.inventory import ListedItem


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

    @property
    def id(self) -> str:
        return self.product_id


@dataclass(frozen=True, slots=True)
class ProductShort(StockXBaseModel):
    product_id: str
    product_name: str = ''
    style_id: str = ''

    @property
    def id(self) -> str:
        return self.product_id


@dataclass(frozen=True, slots=True)
class Variant(StockXBaseModel):
    variant_id: str
    product_id: str
    variant_name: str = ''
    variant_value: str = ''

    @property
    def id(self) -> str:
        return self.variant_id


@dataclass(frozen=True, slots=True)
class VariantShort(StockXBaseModel):
    variant_id: str
    variant_name: str = ''
    variant_value: str = ''    

    @property
    def id(self) -> str:
        return self.variant_id
    

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

    @property
    def transaction_fee(self) -> float:
        for fee in self.adjustments:
            if 'Transaction Fee' in fee.adjustment_type:
                return fee.percentage

    @property
    def payment_fee(self) -> float:
        for fee in self.adjustments:
            if 'Payment Proc' in fee.adjustment_type:
                return fee.percentage
            
    @property
    def shipping_cost(self) -> float:
        for fee in self.adjustments:
            if 'Shipping' in fee.adjustment_type:
                return fee.amount


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
    listing_id: str = ''
    operation_id: str = ''
    operation_type: str = ''
    operation_status: str = ''
    operation_initiated_by: str = ''
    operation_initiated_via: str = ''
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def id(self) -> str:
        return self.operation_id
    
    @property
    def status(self) -> str:
        return self.operation_status
    # TODO: changes, operation_url?


@dataclass(frozen=True, slots=True)
class Listing(StockXBaseModel):
    listing_id: str
    status: str
    amount: float
    currency_code: str
    product: ProductShort
    variant: VariantShort | None = None # TODO: probably required
    inventory_type: str = ''
    order: OrderShort | None = None
    authentication_details: AuthenticationDetails | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def id(self) -> str:
        return self.listing_id

    @property
    def variant_value(self):
        return self.variant.variant_value
    
    @property
    def style_id(self):
        return self.product.style_id


@dataclass(frozen=True, slots=True)
class ListingDetail(Listing):
    payout: Payout | None = None
    last_operation: Operation | None = None


@dataclass(frozen=True, slots=True)
class BatchStatus(StockXBaseModel):
    batch_id: str
    status: str
    total_items: int
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    item_statuses: BatchItemStatuses | None = None


@dataclass(frozen=True, slots=True)
class BatchItemStatuses(StockXBaseModel):
    queued: int | None = None
    failed: int | None = None
    succeeded: int | None = None # TODO is it succeeded or what?


@dataclass(frozen=True, slots=True)
class BatchResultBase(StockXBaseModel):
    item_id: str
    status: str
    result: BatchItemResult | None = None
    error: str = ''

    @property
    def listing_id(self) -> str | None:
        if self.result.listing_id:
            return self.result.listing_id
        return None


@dataclass(frozen=True, slots=True)
class BatchCreateResult(BatchResultBase):
    listing_input: BatchCreateInput


@dataclass(frozen=True, slots=True)
class BatchDeleteResult(BatchResultBase):
    listing_input: BatchDeleteInput


@dataclass(frozen=True, slots=True)
class BatchUpdateResult(BatchResultBase):
    listing_input: BatchUpdateInput


@dataclass(frozen=True, slots=True)
class BatchCreateInput(StockXBaseModel):
    variant_id: str
    amount: float
    quantity: int | None = None
    active: bool | None = None
    currency_code: str = ''
    expires_at: datetime | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            'active': bool(self.active),
            'quantity': int(self.quantity),
            'currencyCode': self.currency_code,
            'variantId': self.variant_id,
            'expiresAt': iso(self.expires_at),
            'amount': str(int(self.amount)) # TODO: check if int or str
        }


@dataclass(frozen=True, slots=True)
class BatchUpdateInput(StockXBaseModel):
    listing_id: str
    active: bool | None = None
    currency_code: str = ''
    expires_at: datetime | None = None
    amount: float | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            'active': bool(self.active),
            'currencyCode': self.currency_code,
            'listingId': self.listing_id,
            'expiresAt': iso(self.expires_at),
            'amount': str(int(self.amount)) # TODO: check if int or str
        }
    
    
@dataclass(frozen=True, slots=True)
class BatchDeleteInput(StockXBaseModel):
    id: str # TODO: check if its id or listing_id in the response  

    @property
    def listing_id(self) -> str:
        return self.id


@dataclass(frozen=True, slots=True)
class BatchItemResult(StockXBaseModel):
    listing_id: str
    ask_id: str = ''