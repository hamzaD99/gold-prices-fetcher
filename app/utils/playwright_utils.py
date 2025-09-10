import uuid
from playwright.sync_api import TimeoutError

async def scroll_until_visible(page, selector, step=500, max_scrolls=20):
    for _ in range(max_scrolls):
        try:
            return await page.wait_for_selector(selector, timeout=1000)
        except TimeoutError:
            await page.evaluate(f"window.scrollBy(0, {step});")
    raise Exception(f"Element not found after {max_scrolls} scrolls")

async def fetch_element_inner_html(name, page, xpath):
    try:
        element = await scroll_until_visible(page, f"xpath={xpath}")
        return await element.inner_html()
    except Exception as e:
        trace_id = uuid.uuid4().hex
        await page.screenshot(path=f"errors_screenshoots/{trace_id}.png")
        print(f"[{trace_id}] Unable to parse the {name}: {e}")