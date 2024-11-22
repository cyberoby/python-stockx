from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base import StockXBaseModel
from ..format import iso


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