from playwright.sync_api import sync_playwright
import time
import os
import asyncio
import platform

def capture_screenshot(url: str, path: str, wait_seconds: int = 3, viewport=(1366, 768), full_page: bool = True) -> str:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    if platform.system() == "Windows":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        page = context.new_page()
        page.goto(url)
        time.sleep(wait_seconds)
        page.screenshot(path=path, full_page=full_page)
        context.close()
        browser.close()
    return path
