from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .base import StockXBaseModel
from .currency import Currency
from ..format import iso
from ..types_ import JSON


class BatchOperationStatus(Enum):
    """Batch operation status codes.

    `QUEUED`
    `IN_PROGRESS`
    `COMPLETED`
    """
    QUEUED = 'QUEUED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'


@dataclass(frozen=True, slots=True)
class BatchStatus(StockXBaseModel):
    """Represents the status of a batch operation.

    Parameters
    ----------
    batch_id : `str`
    status : `str`
    total_items : `int`
    created_at : `datetime`
    updated_at : `datetime` | `None`
    completed_at : `datetime` | `None`
    item_statuses : `BatchItemStatuses` | `None`
    """
    batch_id: str
    status: BatchOperationStatus
    total_items: int
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    item_statuses: BatchItemStatuses | None = None


@dataclass(frozen=True, slots=True)
class BatchItemStatuses(StockXBaseModel):
    """Status counts for items in a batch operation.

    Parameters
    ----------
    queued : `int`
    completed : `int`
    failed : `int`
    """
    queued: int = 0
    completed: int = 0
    failed: int = 0


class BatchItemStatus(Enum):
    """Batch item status codes.

    `QUEUED`
    `COMPLETED`
    `FAILED`
    """
    QUEUED = 'QUEUED'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


@dataclass(frozen=True, slots=True)
class BatchResultBase(StockXBaseModel):
    """Base class for batch operation results.

    Parameters
    ----------
    item_id : `str`
    status : `str`
    result : `BatchItemResult` | `None`
    error : `str`

    Attributes
    ----------
    listing_id : `str` | `None`
    """
    item_id: str
    status: BatchItemStatus
    result: BatchItemResult | None = None
    error: str = ""

    @property
    def listing_id(self) -> str | None:
        if self.result.listing_id:
            return self.result.listing_id
        return None


@dataclass(frozen=True, slots=True)
class BatchCreateResult(BatchResultBase):
    """Result item of a batch create operation.

    Parameters
    ----------
    item_id : `str`
    status : `str`
    result : `BatchItemResult` | `None`
    error : `str`
    listing_input : `BatchCreateInput` | `None`
    """
    listing_input: BatchCreateInput | None = None


@dataclass(frozen=True, slots=True)
class BatchDeleteResult(BatchResultBase):
    """Result item of a batch delete operation.

    Parameters
    ----------
    item_id : `str`
    status : `str`
    result : `BatchItemResult` | `None`
    error : `str`
    listing_input : `BatchDeleteInput` | `None`
    """
    listing_input: BatchDeleteInput | None = None


@dataclass(frozen=True, slots=True)
class BatchUpdateResult(BatchResultBase):
    """Result item of a batch update operation.

    Parameters
    ----------
    item_id : `str`
    status : `str`
    result : `BatchItemResult` | `None`
    error : `str`
    listing_input : `BatchUpdateInput` | `None`
    """
    listing_input: BatchUpdateInput | None = None


@dataclass(frozen=True, slots=True)
class BatchCreateInput(StockXBaseModel):
    """Input item for creating a batch listing.

    Parameters
    ----------
    variant_id : `str`
    amount : `float`
    quantity : `int` | `None`
    active : `bool`
    currency_code : `Currency` | `None`
    expires_at : `datetime` | `None`

    Methods
    -------
    to_json() -> `JSON`
    """
    variant_id: str
    amount: float
    quantity: int | None = None
    active: bool = True
    currency_code: Currency | None = None
    expires_at: datetime | None = None

    def to_json(self) -> JSON:
        data = {
            'variantId': self.variant_id,
            'quantity': int(self.quantity),
            'amount': str(int(self.amount)),
            'expiresAt': iso(self.expires_at),
            'currencyCode': self.currency_code.value if self.currency_code else None,
            'active': self.active,
        }
        return {key: value for key, value in data.items() if value is not None}


@dataclass(frozen=True, slots=True)
class BatchUpdateInput(StockXBaseModel):
    """Input item for updating a batch listing.

    Parameters
    ----------
    listing_id : `str`
    active : `bool` | `None`
    currency_code : `Currency` | `None`
    expires_at : `datetime` | `None`
    amount : `float` | `None`

    Methods
    -------
    to_json() -> `JSON`
    """
    listing_id: str
    active: bool | None = None
    currency_code: Currency | None = None
    expires_at: datetime | None = None
    amount: float | None = None

    def to_json(self) -> JSON:
        data = {
            'listingId': self.listing_id,
            'amount': str(int(self.amount)),
            'expiresAt': iso(self.expires_at),
            'currencyCode': self.currency_code.value if self.currency_code else None,
            'active': self.active,
        }
        return {key: value for key, value in data.items() if value is not None}


@dataclass(frozen=True, slots=True)
class BatchDeleteInput(StockXBaseModel):
    """Input item for deleting a batch listing.

    Parameters
    ----------
    id : `str`

    Attributes
    ----------
    listing_id : `str`
    """
    id: str

    @property
    def listing_id(self) -> str:
        return self.id


@dataclass(frozen=True, slots=True)
class BatchItemResult(StockXBaseModel):
    """Listing ID for a batch operation result item.

    Parameters
    ----------
    listing_id : `str`
    ask_id : `str`
    """
    listing_id: str
    ask_id: str = ""
