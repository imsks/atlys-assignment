from typing import Dict

class InMemoryCache:
    """
    A simple in-memory cache to store product data and check if product price changed.
    We will store products by their title or some unique ID as key.
    """
    def __init__(self):
        # Let's store data in a dict: { "product_title": float_price }
        self.cache: Dict[str, float] = {}

    def get_price(self, product_title: str) -> float:
        return self.cache.get(product_title, None)

    def update_price(self, product_title: str, product_price: float):
        self.cache[product_title] = product_price