from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .base import StockXBaseModel
from .currency import Currency
from .products import ProductShort, VariantShort
    

@dataclass(frozen=True, slots=True)
class Shipment(StockXBaseModel):
    """Sales order shipment.

    Parameters
    ----------
    tracking_number : `str`
    ship_by_date : `datetime` | `None`
    tracking_url : `str`
    carrier_code : `str`
    shipping_label_url : `str`
    shipping_document_url : `str`
    """
    tracking_number: str
    ship_by_date: datetime | None = None
    tracking_url: str = ''
    carrier_code: str = ''
    shipping_label_url: str = ''
    shipping_document_url: str = ''


@dataclass(frozen=True, slots=True)
class AuthenticationDetails(StockXBaseModel):
    """Authentication status details.

    Parameters
    ----------
    status : `str`
    failure_notes : `str`
    """
    status: str = ''
    failure_notes: str = ''


@dataclass(frozen=True, slots=True)
class Adjustments(StockXBaseModel):
    """Fee adjustment information.

    Parameters
    ----------
    adjustment_type : `str`
    amount : `float`
    percentage : `float`
    """
    adjustment_type: str = ''
    amount: float = 0
    percentage: float = 0


@dataclass(frozen=True, slots=True)
class Payout(StockXBaseModel):
    """Payout details.

    Parameters
    ----------
    total_payout : `float`
    sale_price : `float` | `None`
    total_adjustments : `float`
    currency_code : `Currency` | `None`
    adjustments : `list[Adjustments]`

    Attributes
    ----------
    transaction_fee : `float`
    payment_fee : `float`
    shipping_cost : `float`
    """
    total_payout: float
    sale_price: float | None = None
    total_adjustments: float = 0
    currency_code: Currency | None = None
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
            

class OrderStatus(Enum):
    """Sales order status codes.

    `CREATED`
    `CCAUTHORIZATIONFAILED`
    `SHIPPED`
    `RECEIVED`
    `AUTHENTICATING`
    `AUTHENTICATED`
    `PAYOUTPENDING`
    `PAYOUTCOMPLETED`
    `SYSTEMFULFILLED`
    `PAYOUTFAILED`
    `SUSPENDED`
    `AUTHFAILED`
    `DIDNOTSHIP`
    `CANCELED`
    `COMPLETED`
    `RETURNED`

    Parameters
    ----------
    value : `str`
        The sales order status code
    """
    CREATED = 'CREATED'
    CCAUTHORIZATIONFAILED = 'CCAUTHORIZATIONFAILED'
    SHIPPED = 'SHIPPED'
    RECEIVED = 'RECEIVED'
    AUTHENTICATING = 'AUTHENTICATING'
    AUTHENTICATED = 'AUTHENTICATED'
    PAYOUTPENDING = 'PAYOUTPENDING'
    PAYOUTCOMPLETED = 'PAYOUTCOMPLETED'
    SYSTEMFULFILLED = 'SYSTEMFULFILLED'
    PAYOUTFAILED = 'PAYOUTFAILED'
    SUSPENDED = 'SUSPENDED'
    AUTHFAILED = 'AUTHFAILED'
    DIDNOTSHIP = 'DIDNOTSHIP'
    CANCELED = 'CANCELED'
    COMPLETED = 'COMPLETED'
    RETURNED = 'RETURNED'


@dataclass(frozen=True, slots=True)
class Order(StockXBaseModel):
    """Sales order.

    Parameters
    ----------
    order_number : `str`
    listing_id : `str`
    amount : `float`
    status : `OrderStatus`
    currency_code : `Currency`
    product : `ProductShort`
    variant : `VariantShort`
    authentication_details : `AuthenticationDetails` | `None`
    payout : `Payout` | `None`
    created_at : `datetime` | `None`
    updated_at : `datetime` | `None`

    Attributes
    ----------
    number : `str`
    """
    order_number: str
    listing_id: str
    amount: float
    status: OrderStatus
    currency_code: Currency
    product: ProductShort
    variant: VariantShort
    authentication_details: AuthenticationDetails | None = None
    payout: Payout | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def number(self) -> str:
        return self.order_number


@dataclass(frozen=True, slots=True)
class OrderDetail(Order):
    """Detailed sales order with shipment information.

    Parameters
    ----------
    order_number : `str`
    listing_id : `str`
    amount : `float`
    status : `OrderStatus`
    currency_code : `Currency`
    product : `ProductShort`
    variant : `VariantShort`
    authentication_details : `AuthenticationDetails` | `None`
    payout : `Payout` | `None`
    created_at : `datetime` | `None`
    updated_at : `datetime` | `None`
    shipment : `Shipment` | `None`

    Attributes
    ----------
    number : `str`
    """
    shipment: Shipment | None = None


@dataclass(frozen=True, slots=True)
class OrderShort(StockXBaseModel):
    """Short version of sales order.

    Parameters
    ----------
    order_number : `str`
    order_status : `OrderStatus` | `None`
    order_created_at : `datetime` | `None`

    Attributes
    ----------
    number : `str`
    status : `OrderStatus` | `None`
    created_at : `datetime` | `None`
    """
    order_number: str
    order_status: OrderStatus | None = None
    order_created_at: datetime | None = None

    @property
    def number(self) -> str:
        return self.order_number
    
    @property
    def status(self) -> OrderStatus | None:
        return self.order_status
    
    @property
    def created_at(self) -> datetime | None:
        return self.order_created_at
    

class OperationStatus(Enum):
    """Operation status codes.

    `PENDING`
    `SUCCEEDED`
    `FAILED`

    Parameters
    ----------
    value : `str`
        The status code string
    """
    PENDING = 'PENDING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'


@dataclass(frozen=True, slots=True)
class Operation(StockXBaseModel):
    """Listing operation.

    Parameters
    ----------
    listing_id : `str`
    operation_id : `str`
    operation_type : `str`
    operation_status : `OperationStatus` | `None`
    operation_initiated_by : `str`
    operation_initiated_via : `str`
    created_at : `datetime` | `None`
    updated_at : `datetime` | `None`
    error : `str` | `None`

    Attributes
    ----------
    id : `str`
    status : `OperationStatus` | `None`
    """
    listing_id: str = ''
    operation_id: str = ''
    operation_type: str = ''
    operation_status: OperationStatus | None = None
    operation_initiated_by: str = ''
    operation_initiated_via: str = ''
    created_at: datetime | None = None
    updated_at: datetime | None = None
    error: str | None = None

    @property
    def id(self) -> str:
        return self.operation_id
    
    @property
    def status(self) -> OperationStatus | None:
        return self.operation_status
    
    # TODO: changes


class ListingStatus(Enum):
    """Listing status codes.

    `ACTIVE`
    `INACTIVE`
    `CANCELED`
    `MATCHED`
    `COMPLETED`

    Parameters
    ----------
    value : `str`
        The listing status code
    """
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    CANCELED = 'CANCELED'
    MATCHED = 'MATCHED'
    COMPLETED = 'COMPLETED'


@dataclass(frozen=True, slots=True)
class Listing(StockXBaseModel):
    """Listing information.

    Parameters
    ----------
    listing_id : `str`
    status : `ListingStatus`
    amount : `float`
    currency_code : `Currency`
    product : `ProductShort`
    variant : `VariantShort`
    inventory_type : `str`
    order : `OrderShort` | `None`
    authentication_details : `AuthenticationDetails` | `None`
    created_at : `datetime` | `None`
    updated_at : `datetime` | `None`

    Attributes
    ----------
    id : `str`
    variant_value : `str`
    style_id : `str`
    """
    listing_id: str
    status: ListingStatus
    amount: float
    currency_code: Currency
    product: ProductShort
    variant: VariantShort
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
    """Detailed listing information with payout and last operation.

    Parameters
    ----------
    listing_id : `str`
    status : `ListingStatus`
    amount : `float`
    currency_code : `Currency`
    product : `ProductShort`
    variant : `VariantShort`
    inventory_type : `str`
    order : `OrderShort` | `None`
    authentication_details : `AuthenticationDetails` | `None`
    created_at : `datetime` | `None`
    updated_at : `datetime` | `None`
    payout : `Payout` | `None`
    last_operation : `Operation` | `None`

    Attributes
    ----------
    id : `str`
    variant_value : `str`
    style_id : `str`
    """
    payout: Payout | None = None
    last_operation: Operation | None = None


