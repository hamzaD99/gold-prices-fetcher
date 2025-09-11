import json
import asyncio
import uuid
from threading import Lock
from app.utils.helpers import import_attribute
from app.utils.logger import info, error

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
                    error("scraper_import_failed", scraper_path=scraper_path, site=site_url, error=str(e))

        info("sites_loaded", count=len(self.sites))
        return self.sites

    async def start_scraping_async(self):
        if not self.sites:
            raise ValueError("No sites loaded. Call load_sites_from_file() first.")

        info("scrape_batch_start", sites=[s["site"] for s in self.sites])
        scraper_trace_ids: list[str] = []
        tasks = []
        for scraper in self.scrapers:
            tid = uuid.uuid4().hex
            scraper_trace_ids.append(tid)
            info("scrape_site_scheduled", trace_id=tid, site=scraper.site)
            tasks.append(scraper.scrape(trace_id=tid))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for scraper, result, tid in zip(self.scrapers, results, scraper_trace_ids):
            if isinstance(result, Exception):
                error("scrape_site_error", trace_id=tid, site=scraper.site, error=str(result))
                output.append((scraper.site, f"Error: {result}", tid))
            else:
                output.append((scraper.site, result, tid))
        info("scrape_batch_end", results_count=len(output))
        return output