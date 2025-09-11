import os
import asyncio
from app.scraper.service import ScraperService
from app.utils.logger import info
from dotenv import load_dotenv

def main():
    load_dotenv()
    scraper_service = ScraperService()
    sites_path = os.path.join(os.path.dirname(__file__), "sites.json")
    info("scrape_run_start", sites_file=sites_path)
    scraper_service.load_sites_from_file(sites_path)
    results = asyncio.run(scraper_service.start_scraping_async())
    for item in results:
        if len(item) == 3:
            site, result, sid = item
            info("scrape_site_result", trace_id=sid, site=site, result=result)
        else:
            site, result = item
            info("scrape_site_result", site=site, result=result)


if __name__ == "__main__":
    main()