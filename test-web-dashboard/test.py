from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://www.baidu.com")
    time.sleep(3)
    page.screenshot(path="baidu_playwright.png")
    browser.close()