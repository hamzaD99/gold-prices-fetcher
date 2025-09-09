import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from backend.utils.helpers import import_attribute
from backend.utils.logging import get_logger, new_trace_id, set_trace_id

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
        log = get_logger(__name__)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.sites = []
        self.scrapers = []
        for entry in data:
            site_url = entry.get("site")
            scraper_path = entry.get("scraper")
            if not site_url or not scraper_path:
                continue
            self.sites.append({"site": site_url, "scraper_path": scraper_path})

            try:
                scraper_class = import_attribute(scraper_path)
                self.scrapers.append(scraper_class(site=site_url))
            except ImportError as e:
                log.error("Scraper import failed", extra={"site": site_url, "scraper": scraper_path, "error": str(e)})

        return self.sites

    def start_scraping(self, max_workers=4):
        if not self.sites:
            raise ValueError("No sites loaded. Call load_sites_from_file() first.")
        
        log = get_logger(__name__)
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_scraper = {executor.submit(self._run_with_trace(scraper)): scraper for scraper in self.scrapers}
            for future in as_completed(future_to_scraper):
                scraper = future_to_scraper[future]
                try:
                    result = future.result()
                    results.append((scraper.site, result))
                except Exception as e:
                    log.exception("Scrape error", extra={"site": scraper.site})
                    results.append((scraper.site, f"Error: {e}"))
        return results

    @staticmethod
    def _run_with_trace(scraper):
        def _runner():
            set_trace_id(new_trace_id())
            logger = get_logger(__name__)
            logger.info("Starting scraper", extra={"site": scraper.site, "scraper": type(scraper).__name__})
            result = scraper.scrape()
            logger.info("Finished scraper", extra={"site": scraper.site, "scraper": type(scraper).__name__})
            return result
        return _runner