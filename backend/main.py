import os
from backend.utils.logging import configure_logging, get_logger, new_trace_id, set_trace_id
from backend.scraper.service import ScraperService


def main():
    configure_logging()
    log = get_logger(__name__)
    set_trace_id(new_trace_id())
    log.info("Starting scrape run")
    scraper_service = ScraperService()
    sites_path = os.path.join(os.path.dirname(__file__), "sites.json")
    scraper_service.load_sites_from_file(sites_path)
    results = scraper_service.start_scraping()
    for site, result in results:
        log.info("Scrape result", extra={"site": site, "result": result})


if __name__ == "__main__":
    main()