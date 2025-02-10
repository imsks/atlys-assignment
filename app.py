from fastapi import FastAPI, Depends, HTTPException, status, Header
from typing import Optional
from scraper import Scraper
from config import ScraperConfig
from storage import JSONFileStorage
from notification import ConsoleNotification
from cache import InMemoryCache

app = FastAPI()

# Static token for authentication
API_TOKEN = "MY_STATIC_TOKEN"

def verify_token(x_token: str = Header(...)):
    if x_token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token."
        )

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/scrape")
def start_scraping(
    limit_pages: Optional[int] = None,
    proxy: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    Endpoint to trigger scraping.
    - limit_pages: limit the number of pages to scrape from the website.
    - proxy: optionally pass in a proxy string to use for scraping.
    - token: static token for authentication (from Header).
    """
    # Prepare config
    config = ScraperConfig(
        limit_pages=limit_pages,
        proxy=proxy,
        retry_attempts=3,
        retry_backoff=2
    )
    
    # Initialize dependencies
    storage_strategy = JSONFileStorage(file_path="database.json")
    notification_strategy = ConsoleNotification()
    cache = InMemoryCache()

    # Create scraper with dependencies
    scraper = Scraper(
        config=config,
        storage=storage_strategy,
        notifier=notification_strategy,
        cache=cache
    )

    # Perform scraping
    scraper.scrape()
    
    return {"message": "Scraping initiated."}