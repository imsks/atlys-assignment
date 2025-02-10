import json
import os
from abc import ABC, abstractmethod
from typing import List
from schemas import Product

class BaseStorage(ABC):
    @abstractmethod
    def save(self, products: List[Product]) -> None:
        pass

    @abstractmethod
    def load(self) -> List[Product]:
        pass


class JSONFileStorage(BaseStorage):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def save(self, products: List[Product]) -> None:
        dict_list = [product.dict() for product in products]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(dict_list, f, indent=2)

    def load(self) -> List[Product]:
        if not os.path.exists(self.file_path):
            return []

        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Product(**item) for item in data]