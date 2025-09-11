from celery import Celery
import os
from dotenv import load_dotenv
import asyncio
from app.scraper.service import ScraperService
from app.utils.logger import info
from app.utils.telegram import send_telegram_message

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Example scraping task
@celery_app.task
def scrape_gold_price():
    load_dotenv()
    scraper_service = ScraperService()
    sites_path = os.path.join(os.path.dirname(__file__), "sites.json")
    info("scrape_run_start", sites_file=sites_path)
    scraper_service.load_sites_from_file(sites_path)
    results = asyncio.run(scraper_service.start_scraping_async())
    valid_prices = []
    valid_sites = []
    invalid_sites = []
    for item in results:
        if len(item) == 3:
            site, result, sid = item
            info("scrape_site_result", trace_id=sid, site=site, result=result)
        else:
            site, result = item
            info("scrape_site_result", site=site, result=result)
        if(result.get("price") != -1):
            valid_prices.append(result.get("price"))
            valid_sites.append(site)
        else:
            invalid_sites.append(site)
    avg_price = sum(valid_prices) / len(valid_prices)
    msg = ''
    if len(valid_sites):
        msg = (
            "📊 <b>Gold Price Update</b>\n\n"
            f"💰 <b>Average Price</b>: ${avg_price:.2f} / gram\n"
            f"📡 <b>Sources Scraped</b>: {', '.join(valid_sites)}"
        )
    if len(invalid_sites):
        msg += f"\n❌ <b>Failed Sources</b>: {', '.join(invalid_sites)}"
    send_telegram_message(msg)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "scrape-every-10-minutes": {
        "task": "app.tasks.scrape_gold_price",
        "schedule": crontab(minute="*/1")
    },
}
celery_app.conf.timezone = "UTC"