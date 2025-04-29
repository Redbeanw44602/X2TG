from playwright.async_api import (
    async_playwright,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from twitter.config import MAIN_URL


async def _run(playwright: Playwright, browser_context: str):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    print('login context has been created, please complete the login within 5 minutes.')

    # login page
    page = await context.new_page()
    await page.goto(MAIN_URL)
    try:
        await page.get_by_test_id('SideNav_AccountSwitcher_Button').wait_for(timeout=5 * 60 * 1000)
    except PlaywrightTimeoutError:
        print('login timeout.')
    else:
        print('login successfully.')
        await context.storage_state(path=browser_context)

    await context.close()
    await browser.close()


async def process(**kwargs):
    async with async_playwright() as playwright:
        await _run(playwright, **kwargs)
