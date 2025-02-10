from pydantic import BaseModel, Field

class Product(BaseModel):
    product_title: str = Field(..., example="Example Product")
    product_price: float = Field(..., example=99.99)
    path_to_image: str = Field(..., example="/path/to/image.jpg")