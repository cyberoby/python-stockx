from stockx.models import Product

async def search_product_by_sku(sku: str) -> Product | None:
    async for product in catalog.search_catalog(query=sku):
        if sku in product.style_id:
            return product
    else:
        return None
    

async def search_product_by_url(stock_url: str) -> Product | None:
    async for product in catalog.search_catalog(query=stock_url):
        if product.url_key in stock_url:
            return product
    else:
        return None