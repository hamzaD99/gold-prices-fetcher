import os
import asyncio
from app.scraper.service import ScraperService

def main():
    scraper_service = ScraperService()
    sites_path = os.path.join(os.path.dirname(__file__), "sites.json")
    scraper_service.load_sites_from_file(sites_path)
    results = asyncio.run(scraper_service.start_scraping_async())
    for site, result in results:
        print(site, result)


if __name__ == "__main__":
    main()