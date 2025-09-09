from abc import ABC, abstractmethod
from backend.utils.logging import get_logger
from playwright.sync_api import sync_playwright

log = get_logger(__name__)

class BaseScraper(ABC):
    site = None

    def __init__(self, site) -> None:
        if site:
            self.site = site

    @abstractmethod
    def scrape(self) -> dict:
        pass

class ExampleComScraper(BaseScraper):
    def scrape(self) -> dict:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(self.site)
            filename = f"{self.site.replace('https://','').replace('http://','').replace('/','_')}.png"
            page.screenshot(path=filename)
            browser.close()
        return {}