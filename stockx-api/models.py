from __future__ import annotations

from dataclasses import dataclass, field

from utils import json_to_snake


@dataclass
class Response:
    status_code: int
    message: str = ''
    data: dict | list[dict] = field(default_factory=list)


@dataclass
class StockXBaseModel:

    @classmethod
    def from_json(cls, json: dict):
        snake_kwargs = json_to_snake(json).items() 
        matching_kwargs = {
            key: value for key, value in snake_kwargs 
            if key in cls.__match_args__
        }
        return cls(**matching_kwargs)


@dataclass
class ProductAttributes(StockXBaseModel):
    gender: str = ''
    season: str = ''
    release_date: str = ''
    retail_price: str = ''
    colorway: str = ''
    color: str = ''


@dataclass
class Product(StockXBaseModel):
    product_id: str
    url_key: str = ''
    style_id: str = ''
    product_type: str = ''
    title: str = ''
    brand: str = ''
    product_attributes: ProductAttributes = None

    def __post_init__(self) -> None:
        if self.product_attributes:
            self.product_attributes = ProductAttributes.from_json(self.product_attributes)
    

@dataclass
class Variant(StockXBaseModel):
    product_id: str
    variant_id: str
    variant_name: str = ''
    variant_value: str = ''


@dataclass
class MarketData(StockXBaseModel):
    product_id: str
    variant_id: str
    currency_code: str
    lowest_ask_amount: int = 0
    highest_bid_amount: int = 0
    sell_faster_amount: int = 0
    earn_more_amount: int = 0
