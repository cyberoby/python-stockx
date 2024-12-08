from __future__ import annotations

from collections.abc import AsyncIterable, Iterable
from typing import TYPE_CHECKING

from ...ext import search
from ...models import Listing

if TYPE_CHECKING:
    from .inventory import Inventory
    from ...api import StockX


class Item:
    """
    Represents an inventory item with product details and quantity.
    
    Provides an abstraction for managing StockX inventory by aggregating
    multiple listings of the same product variant and price into a single 
    inventory entry with a combined quantity, simplifying inventory management.

    Parameters
    ----------
    product_id : `str`
        The Product ID of the item.
    variant_id : `str`
        The Variant ID of the item.
    price : `float`
        The listing (or Ask) amount of the item.
    quantity : `int`, optional
        The quantity of the item, by default 1.

    Notes
    -----
    When selling products on StockX, each listing represents a single item
    (quantity=1) and is handled independently. This class consolidates these
    individual listings into a more traditional inventory model where
    identical items (same variant and price) are grouped together with a
    cumulative quantity.
    """

    __slots__ = '_price', '_quantity', 'product_id', 'variant_id',

    def __init__(
            self,
            product_id: str,
            variant_id: str,
            price: float,
            quantity: int = 1,
    ) -> None:
        self.product_id = product_id
        self.variant_id = variant_id
        self.price = price
        self.quantity = quantity

    @classmethod
    async def from_sku_size(
            cls,
            stockx: StockX,
            sku: str,
            size: str,
            price: float,
            quantity: int = 1
    ) -> Item | None:
        """
        Create an Item instance from SKU and size information.

        Parameters
        ----------
        stockx : `StockX`
            The StockX API interface instance.
        sku : `str`
            The product SKU (StockX Style ID).
        size : `str`
            The product's US size.
        price : `float`
            The price of the item.
        quantity : `int`, optional
            The quantity of the item, by default 1.

        Returns
        -------
        `Item` | `None`
            The created `Item` instance, or `None` if a product variant 
            is not found for the given SKU and size.
        """
        product = await search.product_by_sku(stockx, sku)

        if not product:
            return None
        
        variants = await stockx.catalog.get_all_product_variants(product.id)
        variant = next(
            (variant for variant in variants if variant.variant_value == size),
            None
        )

        if not variant:
            return None
        
        return cls(
            product_id=product.id,
            variant_id=variant.id,
            price=price,
            quantity=quantity
        )

    @property
    def price(self) -> float:
        return self._price
    
    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError('Price must be greater than 0.')
        self._price = value

    @property
    def quantity(self) -> int:
        return self._quantity
    
    @quantity.setter
    def quantity(self, value: int) -> None:
        if value < 0:
            raise ValueError('Quantity must be greater than 0.') 
        if int(value) != value:
            raise ValueError('Quantity must be an integer.')   
        self._quantity = value

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'{self.product_id=}, '
            f'{self.variant_id=}, '
            f'{self.price=}, '
            f'{self.quantity=})'
        ).replace('self.', '')
    
    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}:\n'
            f'  product_id: {self.product_id}\n'
            f'  variant_id: {self.variant_id}\n'
            f'  price: {self.price}\n'
            f'  quantity: {self.quantity}'
        )

    
class ListedItem:
    """
    Represents an item that has been listed on StockX.

    Parameters
    ----------
    item : `Item`
        The base item instance.
    inventory : `Inventory`
        The inventory this item belongs to.
    listing_ids : `Iterable[str]`
        Collection of listing IDs associated with this item.

    Attributes
    ----------
    product_id : `str`
    variant_id : `str`
    price : `float`
    quantity : `int`
    style_id : `str`
    size : `str`
    name : `str`

    Methods
    -------
    quantity_to_sync() -> `int`
        Number of listings to publish (if positive) or delete (if negative).
    payout() -> `float`
        Calculated payout amount for this item.
    """

    __slots__ = (
        '_inventory', 
        '_item', 
        '_name', 
        '_size', 
        '_style_id', 
        'listing_ids',
    )

    def __init__(
            self,
            item: Item,
            inventory: Inventory,
            listing_ids: Iterable[str],
    ) -> None:
        self._item = item
        self._inventory = inventory
        self._item.quantity = len(listing_ids)
        self.listing_ids = list(listing_ids)

        self._style_id = None
        self._size = None
        self._name = None

    @classmethod
    async def from_inventory_listings(
            cls, 
            inventory: Inventory,
            listings: AsyncIterable[Listing]
    ) -> list[ListedItem]:
        """
        Create ListedItem instances from inventory listings.

        Parameters
        ----------
        inventory : `Inventory`
            The inventory instance.
        listings : `AsyncIterable[Listing]`
            Async iterable of listings to process.

        Returns
        -------
        `list[ListedItem]`
            List of created ListedItem instances.
        """
        items: dict[str, dict[float, ListedItem]] = {}

        async for listing in listings:
            amounts_dict = items.setdefault(listing.variant.id, {})
            
            if listing.amount in amounts_dict:
                amounts_dict[listing.amount]._item.quantity += 1 
                amounts_dict[listing.amount].listing_ids.append(listing.id)
            else:
                item = ListedItem(
                    item=Item(
                        product_id=listing.product.id, 
                        variant_id=listing.variant.id, 
                        price=listing.amount, 
                    ),
                    inventory=inventory,
                    listing_ids=[listing.id]
                )
                item._style_id = listing.style_id
                item._size = listing.variant_value
                item._name = listing.product.product_name

                amounts_dict[listing.amount] = item

        return [item for amount in items.values() for item in amount.values()]
    
    @property
    def product_id(self) -> str:
        """The Product ID of this item."""
        return self._item.product_id

    @property
    def variant_id(self) -> str:
        """The Variant ID of this item."""
        return self._item.variant_id
    
    @property
    def price(self) -> float:
        """The listing (or Ask) amount this item is listed at."""
        return self._item.price
    
    @price.setter
    def price(self, value: float) -> None:
        if value != self.price:
            self._item.price = value
            self._inventory.register_price_change(self)
    
    @property
    def quantity(self) -> int:
        """The current quantity of listings."""
        return self._item.quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if value != self.quantity:
            self._item.quantity = value
            self._inventory.register_quantity_change(self)

    @property
    def style_id(self) -> str | None:
        """The Style ID of the product (if available)."""
        return self._style_id
    
    @property
    def size(self) -> str | None:
        """The size of the product variant (if available)."""
        return self._size
    
    @property
    def name(self) -> str | None:
        """The product name (if available)."""
        return self._name
    
    def quantity_to_sync(self) -> int:
        """
        Number of listings to publish (if positive) or delete (if negative).
        """
        return self.quantity - len(self.listing_ids)
    
    def payout(self) -> float:
        """Calculated payout amount for this item."""
        return self._inventory.calculate_payout(self.price)
    
    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'{self._item=}, '
            f'{self._inventory=}, '
            f'{self.listing_ids=}, '
        ).replace('self._', '').replace('self.', '')
    
    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}:\n'
            f'  product_id: {self.product_id}\n'
            f'  variant_id: {self.variant_id}\n'
            f'  price: {self.price}\n'
            f'  payout: {self.payout()}\n'
            f'  quantity: {self.quantity}\n'
            f'  style_id: {self.style_id}\n'
            f'  size: {self.size}\n'
            f'  name: {self.name}\n'
            f'  listing_ids: {', '.join(self.listing_ids)}'
        )

