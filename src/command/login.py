from playwright.sync_api import sync_playwright, Playwright, TimeoutError as PlaywrightTimeoutError


def _run(playwright: Playwright, state_path: str):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    print('login context has been created, please complete the login within 5 minutes.')

    # login page
    page = context.new_page()
    page.goto('https://x.com/')
    try:
        page.get_by_test_id('SideNav_AccountSwitcher_Button').wait_for(timeout=5 * 60 * 1000)
    except PlaywrightTimeoutError:
        print('login timeout.')
    else:
        print('login successfully.')
        context.storage_state(path=state_path)

    context.close()
    browser.close()


def process(state_path: str):
    with sync_playwright() as playwright:
        _run(playwright, state_path)
