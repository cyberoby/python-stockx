from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from .base import StockXBaseModel
from .products import ProductShort, VariantShort
    

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


