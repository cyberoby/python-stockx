from contextlib import asynccontextmanager


@asynccontextmanager
async def mock_listing(inventory: Inventory, amount: float = 1000): # TODO: change inventory with stockx, type hint
    product = await anext(inventory.catalog.search_catalog('adidas'))
    variants = await inventory.catalog.get_all_product_variants(product.id)
    create = await inventory.listings.create_listing(
        amount=amount,
        variant_id=variants[0].id,
        currency_code=inventory.currency,
    )
    if not await inventory.listings.operation_succeeded(create):
        pass # raise what?
    
    try:
        listing = await inventory.listings.get_listing(create.listing_id)
        yield listing
    finally:
        delete = await inventory.listings.delete_listing(create.listing_id)
        if not await inventory.listings.operation_succeeded(delete):
            pass # log