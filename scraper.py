import time
import traceback
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
        pages_to_scrape = self.config.limit_pages

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
        if page == 1:
            url = "https://dentalstall.com/shop/"
        else:
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
        return self._extract_products_from_html(response.text)
    
    # I've got Whole HTML response in response.text
    # Now I will use BeautifulSoup to extract the fields
    # First Select Whole Products Container by ID -> mf-shop-content
    # You'll get a UL Tag and Inside All LI Tags are Products
    # Loop through all LI Tags and Extract Product Title, Price, Image URL
    # Each Product will have a product-inner class
    # Then 2 More classes - mf-product-thumbnail for Image and mf-product-details for Title and Price
    # Extract Image URL from mf-product-thumbnail using img tag
    # Extract Title from mf-product-details using h2 tag
    # Extract Price from mf-product-details using span tag with class="woocommerce-Price-currencySymbol" but note that it's deeply nested 
    # Create a Method to work on this HTML and return a List of Product Objects
    def _extract_products_from_html(self, response_text: str) -> List[Product]:
        """
        Extracts product information from the given HTML response text.
        
        Steps:
        1. Parse the HTML with BeautifulSoup using the lxml parser.
        2. Find the UL element with id "mf-shop-content" (the products container).
        3. Loop through each LI element (each product) inside the container.
        4. For each product:
            - Find the element with class "product-inner".
            - Within that, locate the image container ("mf-product-thumbnail") and extract the img tag's src.
            - Locate the details container ("mf-product-details") and:
                * Extract the product title from the h2 tag.
                * Extract the product price by finding a span with class "woocommerce-Price-currencySymbol",
                then use its parent element’s text to extract a numeric value (price).
        5. Return a list of Product objects.
        """
        from bs4 import BeautifulSoup
        import re

        try:
            soup = BeautifulSoup(response_text, "lxml")
            products = []

            # Find the container holding the product list by its id
            container = soup.find(id="mf-shop-content")
            if container is None:
                # If container is not found, return empty list
                return products

            # Each product is expected to be inside an LI tag within the container
            product_items = container.find_all("li")
            for item in product_items:
                # Find the inner container that holds product details
                product_inner = item.find(class_="product-inner")
                if not product_inner:
                    continue

                # --- Extract the image URL ---
                image_url = ""
                thumbnail = product_inner.find(class_="mf-product-thumbnail")
                if thumbnail:
                    img_tag = thumbnail.find("img", class_="attachment-woocommerce_thumbnail")
                    if img_tag:
                        image_url = img_tag.get("data-lazy-src", "")
                        print("HERE", image_url)


                # --- Extract title and price ---
                title = ""
                price = 0.0
                details = product_inner.find(class_="mf-product-details")
                if details:
                    # Extract the product title from an h2 tag
                    h2_tag = details.find("h2")
                    if h2_tag:
                        title = h2_tag.get_text(strip=True)

                    # Extract the product price by locating the span with the currency symbol
                    price_span = details.find("span", class_="woocommerce-Price-currencySymbol")
                    if price_span:
                        # Assume that the parent of the currency span holds the full price text
                        price_text = price_span.parent.get_text(strip=True)
                        # Use regex to find a numeric value (which may be a float)
                        match = re.search(r"(\d+(?:\.\d+)?)", price_text)
                        if match:
                            price = float(match.group(1))

                # Create and append the product if a title was found
                if title:
                    products.append(Product(
                        product_title=title,
                        product_price=price,
                        path_to_image=image_url
                    ))

            return products   
        except Exception as e:
            print(traceback.print_exc())
            return [] 