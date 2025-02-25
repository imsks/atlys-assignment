from pydantic import BaseModel, PositiveInt
from typing import Optional

class ScraperConfig(BaseModel):
    limit_pages: Optional[PositiveInt] = None or 2
    proxy: Optional[str] = None
    retry_attempts: int = 3
    retry_backoff: int = 2