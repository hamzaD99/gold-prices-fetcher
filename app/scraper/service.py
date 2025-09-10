import json
import asyncio
from threading import Lock
from app.utils.helpers import import_attribute

class ScraperService:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'sites'):
            self.sites = []

    def load_sites_from_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.sites = []
        self.scrapers = []
        for entry in data:
            if entry.get("scrape", False):
                site_url = entry.get("site")
                scraper_path = entry.get("scraper")
                if not site_url or not scraper_path:
                    continue
                self.sites.append({"site": site_url, "scraper_path": scraper_path})

                try:
                    scraper_class = import_attribute(scraper_path)
                    self.scrapers.append(scraper_class(site=site_url))
                except ImportError as e:
                    print(f"Can't import {scraper_path} for {site_url}: {e}")

        return self.sites

    async def start_scraping_async(self):
        if not self.sites:
            raise ValueError("No sites loaded. Call load_sites_from_file() first.")

        tasks = [scraper.scrape() for scraper in self.scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for scraper, result in zip(self.scrapers, results):
            if isinstance(result, Exception):
                output.append((scraper.site, f"Error: {result}"))
            else:
                output.append((scraper.site, result))
        return output