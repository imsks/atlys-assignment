from typing import Dict

class InMemoryCache:
    def __init__(self):
        self.cache: Dict[str, float] = {}

    def get_price(self, product_title: str) -> float:
        return self.cache.get(product_title, None)

    def update_price(self, product_title: str, product_price: float):
        self.cache[product_title] = product_price