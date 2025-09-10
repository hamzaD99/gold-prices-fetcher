import time
import re
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from decimal import Decimal
from app.utils.playwright_utils import fetch_element_inner_html
from app.utils.helpers import convert_oz_price_gm
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


class BaseScraper(ABC):
    site = None

    def __init__(self, site) -> None:
        if site:
            self.site = site

    @abstractmethod
    def scrape(self) -> dict:
        pass

class GoldPriceOrgScraper(BaseScraper):
    async def scrape(self) -> dict:
        result = {
            "price": -1,
            "time": -1
        }
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.site)
            price_element = await fetch_element_inner_html(name="price_element", page=page, xpath="/html/body/main/div[2]/div/div/div[2]/div/article/div/div[3]/div[2]/div[1]/div/div/div/table/tbody/tr[2]/td[2]")
            result["price"] = Decimal(price_element) if price_element else -1
            
            time_str = await fetch_element_inner_html(name="time_element", page=page, xpath="/html/body/main/div[2]/div/div/div[2]/div/article/div/div[3]/div[2]/div[1]/div/div/div/table/tfoot/tr/td/div")
            if time_str:
                cleaned = time_str.replace("th", "").replace(" NY time", "")
                dt_local = datetime.strptime(cleaned, "%b %d %Y, %I:%M:%S %p")
                dt_ny = dt_local.replace(tzinfo=ZoneInfo("America/New_York"))
                dt_utc = dt_ny.astimezone(ZoneInfo("UTC"))
                result["time"] = dt_utc.timestamp()
            else:
                result["time"] = time.time()
            await browser.close()
        return result


class TradingEconomicsComScraper(BaseScraper):
    async def scrape(self) -> dict:
        result = {
            "price": -1,
            "time": -1
        }
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.site)
            table_element = await fetch_element_inner_html(name="table_element", page=page, xpath="/html/body/form/div[5]/div/div[1]/div[4]/div/div/table")
            price_str = self.fetch_gold_price_from_table(table_element) if table_element else None
            result["price"] = convert_oz_price_gm(Decimal(price_str.replace(',', ''))) if price_str else -1
            result["time"] = time.time()
            await browser.close()
        return result
    
    def fetch_gold_price_from_table(self, table_html):
        soup = BeautifulSoup(table_html, "html.parser")
        gold_row = soup.find("tr", {"data-symbol": "XAUUSD:CUR"})
        if gold_row:
            price_cell = gold_row.find("td", {"id": "p"})
            return price_cell.get_text(strip=True)

class BullionVaultComScraper(BaseScraper):
    async def scrape(self) -> dict:
        result = {
            "price": -1,
            "time": -1
        }
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.site)
            price_str = None
            for _ in range(10):
                table_element = await fetch_element_inner_html(name="table_element", page=page, xpath="/html/body/main/div[2]/div[3]/div[1]/div/div/div/table")
                price_str, time_str = self.fetch_price_and_time_from_table(table_element) if table_element else None
                if price_str:
                    break
                time.sleep(5)
            result["price"] = Decimal(price_str.replace("$", "").replace(",", "")) if price_str else -1
            result["time"] = self.convert_to_timestamp(time_str) if time_str else time.time()
            await browser.close()
        return result
    
   
    def fetch_price_and_time_from_table(self, table_html):
        soup = BeautifulSoup(table_html, "html.parser")
        gold_row = None
        for tr in soup.find_all("tr"):
            th = tr.find("th")
            if th and "Gold Price per Gram" in th.get_text():
                gold_row = tr
                break

        price = None
        if gold_row:
            price_span = gold_row.find("span", {"data-weight": "G", "data-currency": "USD"})
            if price_span:
                price = price_span.get_text(strip=True)

        time_row = soup.find("td", class_="bullion-price-timestamp")
        timestamp = None
        if time_row:
            timestamp = time_row.get_text(strip=True)

        return price, timestamp
    
    def convert_to_timestamp(self, time_str):
        match = re.search(r"\(GMT([+-]\d{2}):(\d{2})\)", time_str)
        if match:
            hours_offset = int(match.group(1))
            minutes_offset = int(match.group(2))
            tz_offset = timezone(timedelta(hours=hours_offset, minutes=minutes_offset))
        else:
            tz_offset = timezone.utc
        time_str_clean = re.sub(r"\s*\(GMT[+-]\d{2}:\d{2}\)", "", time_str)
        dt = datetime.strptime(time_str_clean, "%d %B %Y, %H:%M:%S")
        dt = dt.replace(tzinfo=tz_offset)
        return dt.timestamp()