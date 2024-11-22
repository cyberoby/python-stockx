from __future__ import annotations
from dataclasses import dataclass

from .base import StockXBaseModel


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