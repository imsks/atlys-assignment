from fastapi import FastAPI, Depends, HTTPException, status, Header
from typing import Optional
from scraper import Scraper
from config import ScraperConfig
from storage import JSONFileStorage
from notification import ConsoleNotification
from cache import InMemoryCache

app = FastAPI()

API_TOKEN = "AtlysAssignmentBySachin"

def verify_token(token: str = Header(...)):
    if token != API_TOKEN:
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
    config = ScraperConfig(
        limit_pages=limit_pages,
        proxy=proxy,
        retry_attempts=3,
        retry_backoff=2
    )
    
    storage_strategy = JSONFileStorage(file_path="database.json")
    notification_strategy = ConsoleNotification()
    cache = InMemoryCache()

    scraper = Scraper(
        config=config,
        storage=storage_strategy,
        notifier=notification_strategy,
        cache=cache
    )

    scraper.scrape()
    
    return {"message": "Scraping initiated."}