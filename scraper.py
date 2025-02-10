import time
import requests
from typing import List
from schemas import Product
from storage import BaseStorage
from notification import BaseNotification
from config import ScraperConfig
from cache import InMemoryCache

class Scraper:
    def __init__(
        self,
        config: ScraperConfig,
        storage: BaseStorage,
        notifier: BaseNotification,
        cache: InMemoryCache
    ):
        self.config = config
        self.storage = storage
        self.notifier = notifier
        self.cache = cache

    def scrape(self):
        """
        Main scraping logic. 
        1. Loads existing data from storage
        2. Scrapes a certain number of pages (if limit_pages is set)
        3. Applies a simple retry mechanism
        4. Updates storage + in-memory cache
        5. Sends notification about how many new/updated products
        """
        existing_products = self.storage.load()
        # Build a dictionary for quick lookups from existing storage
        existing_dict = {prod.product_title: prod for prod in existing_products}

        # Let's do a dummy scrape for demonstration
        # In a real scenario, you might use requests+BeautifulSoup to parse HTML
        # We'll simulate N "pages" each with 2 products
        scraped_products = []
        pages_to_scrape = self.config.limit_pages or 2  # default to 2 pages if not set

        for page in range(1, pages_to_scrape + 1):
            # Attempt to scrape with retry
            page_products = self._scrape_page_with_retry(page)
            scraped_products.extend(page_products)

        # Now let's figure out which of these products are new or updated
        updated_count = 0

        for product in scraped_products:
            cached_price = self.cache.get_price(product.product_title)
            if cached_price is not None:
                # product has been seen before in the cache
                if abs(cached_price - product.product_price) > 1e-9:
                    # Price changed, so we update storage + cache
                    existing_dict[product.product_title] = product
                    self.cache.update_price(product.product_title, product.product_price)
                    updated_count += 1
            else:
                # first time seeing this product in the cache
                # check if it's in existing storage
                if product.product_title not in existing_dict:
                    # new product
                    existing_dict[product.product_title] = product
                    self.cache.update_price(product.product_title, product.product_price)
                    updated_count += 1
                else:
                    # in storage but not in cache? Let's populate cache and see if price changed
                    stored_price = existing_dict[product.product_title].product_price
                    self.cache.update_price(product.product_title, stored_price)
                    if abs(stored_price - product.product_price) > 1e-9:
                        # update if changed
                        existing_dict[product.product_title] = product
                        self.cache.update_price(product.product_title, product.product_price)
                        updated_count += 1

        # Save updated dictionary back to storage
        final_list = list(existing_dict.values())
        self.storage.save(final_list)

        # Send notification about how many items were updated
        message = f"Scraped {len(scraped_products)} products. Updated {updated_count} in DB."
        self.notifier.send(message)

    def _scrape_page_with_retry(self, page: int):
        """
        Demonstrates a simple retry mechanism with backoff.
        Returns a list of Product objects from a single page.
        """
        attempts = self.config.retry_attempts
        backoff = self.config.retry_backoff

        for attempt in range(attempts):
            try:
                products = self._scrape_single_page(page)
                return products
            except requests.RequestException as e:
                print(f"Error scraping page {page}: {str(e)}")
                if attempt < attempts - 1:
                    time.sleep(backoff)
                else:
                    # Reraise or handle differently if all attempts fail
                    raise e
        return []

    def _scrape_single_page(self, page: int) -> List[Product]:
        """
        Actual page-scraping logic.
        Stubbed here with sample data.
        If using a proxy, you'd do:
            proxies = {"http": self.config.proxy, "https": self.config.proxy}
            response = requests.get(url, proxies=proxies, timeout=10)
        """
        # Example with or without proxy
        url = f"https://dentalstall.com/shop/page/{page}/"
        proxies = None
        if self.config.proxy:
            proxies = {
                "http": self.config.proxy,
                "https": self.config.proxy
            }

        # Make a GET request
        response = requests.get(url, proxies=proxies, timeout=5)
        response.raise_for_status()

        # Dummy data to emulate product extraction
        # In real scenario: parse `response.text` with BeautifulSoup to extract fields
        sample_products = [
            Product(
                product_title=f"Product Page{page}-A",
                product_price=100.0 + page,
                path_to_image=f"/path/to/image-{page}-A.jpg"
            ),
            Product(
                product_title=f"Product Page{page}-B",
                product_price=150.5 + page,
                path_to_image=f"/path/to/image-{page}-B.jpg"
            ),
        ]

        return sample_products