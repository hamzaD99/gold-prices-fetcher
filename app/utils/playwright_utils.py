import os
import uuid
from playwright.sync_api import TimeoutError
from app.utils.logger import error, info

async def scroll_until_visible(page, selector, step=500, max_scrolls=20):
    for _ in range(max_scrolls):
        try:
            return await page.wait_for_selector(selector, timeout=1000)
        except TimeoutError:
            await page.evaluate(f"window.scrollBy(0, {step});")
    raise Exception(f"Element not found after {max_scrolls} scrolls")

async def fetch_element_inner_html(name, page, xpath, *, trace_id=None, page_url=None):
    try:
        element = await scroll_until_visible(page, f"xpath={xpath}")
        html = await element.inner_html()
        info("element_parsed", trace_id=trace_id, name=name, xpath=xpath)
        return html
    except Exception as e:
        sid = trace_id or uuid.uuid4().hex
        os.makedirs("errors_screenshoots", exist_ok=True)
        screenshot_path = f"errors_screenshoots/{sid}.png"
        try:
            await page.screenshot(path=screenshot_path)
        except Exception:
            screenshot_path = None
        error(
            "element_parse_error",
            trace_id=sid,
            name=name,
            xpath=xpath,
            page_url=page_url,
            screenshot=screenshot_path,
            error=str(e),
        )