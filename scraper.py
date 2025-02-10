import time
import traceback
import requests
from typing import List
from schemas import Product
from storage import BaseStorage
from notification import BaseNotification
from config import ScraperConfig
from cache import InMemoryCache
from bs4 import BeautifulSoup
import re

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
        existing_products = self.storage.load()
        existing_dict = {prod.product_title: prod for prod in existing_products}

        scraped_products = []
        pages_to_scrape = self.config.limit_pages

        for page in range(1, pages_to_scrape + 1):
            page_products = self._scrape_page_with_retry(page)
            scraped_products.extend(page_products)

        updated_count = 0

        for product in scraped_products:
            cached_price = self.cache.get_price(product.product_title)
            if cached_price is not None:
                if abs(cached_price - product.product_price) > 1e-9:
                    existing_dict[product.product_title] = product
                    self.cache.update_price(product.product_title, product.product_price)
                    updated_count += 1
            else:
                if product.product_title not in existing_dict:
                    existing_dict[product.product_title] = product
                    self.cache.update_price(product.product_title, product.product_price)
                    updated_count += 1
                else:
                    stored_price = existing_dict[product.product_title].product_price
                    self.cache.update_price(product.product_title, stored_price)
                    if abs(stored_price - product.product_price) > 1e-9:
                        existing_dict[product.product_title] = product
                        self.cache.update_price(product.product_title, product.product_price)
                        updated_count += 1

        final_list = list(existing_dict.values())
        self.storage.save(final_list)

        message = f"Scraped {len(scraped_products)} products. Updated {updated_count} in DB."
        self.notifier.send(message)

    def _scrape_page_with_retry(self, page: int):
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
                    raise e
        return []

    def _scrape_single_page(self, page: int) -> List[Product]:
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

        response = requests.get(url, proxies=proxies, timeout=5)
        response.raise_for_status()

        return self._extract_products_from_html(response.text)
    
    def _extract_products_from_html(self, response_text: str) -> List[Product]:
        try:
            soup = BeautifulSoup(response_text, "lxml")
            products = []

            container = soup.find(id="mf-shop-content")
            if container is None:
                return products

            product_items = container.find_all("li")
            for item in product_items:
                product_inner = item.find(class_="product-inner")
                if not product_inner:
                    continue

                image_url = ""
                thumbnail = product_inner.find(class_="mf-product-thumbnail")
                if thumbnail:
                    img_tag = thumbnail.find("img", class_="attachment-woocommerce_thumbnail")
                    if img_tag:
                        image_url = img_tag.get("data-lazy-src", "")
                        print("HERE", image_url)


                title = ""
                price = 0.0
                details = product_inner.find(class_="mf-product-details")
                if details:
                    h2_tag = details.find("h2")
                    if h2_tag:
                        title = h2_tag.get_text(strip=True)

                    price_span = details.find("span", class_="woocommerce-Price-currencySymbol")
                    if price_span:
                        price_text = price_span.parent.get_text(strip=True)
                        match = re.search(r"(\d+(?:\.\d+)?)", price_text)
                        if match:
                            price = float(match.group(1))

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