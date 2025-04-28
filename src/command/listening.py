import re
import json

from playwright.sync_api import sync_playwright, Playwright, Request

from twitter.instruction.parser import InstructionParser


def _run(playwright: Playwright, state_path: str, username: str):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state=state_path)
    print('context has been restored.')

    # home page
    page = context.new_page()
    page.on('request', _on_request)

    page.goto(f'https://x.com/{username}', timeout=15 * 1000)

    try:
        avatar_frame = page.get_by_test_id('SideNav_AccountSwitcher_Button')
        assert avatar_frame.count() != 0, 'login expired.'

        # wait for tweets
        page.get_by_test_id('tweet').first.wait_for(timeout=12 * 1000)

    except Exception as e:
        raise e

    context.storage_state(path=state_path)
    context.close()
    browser.close()


def _on_request(req: Request):
    if not re.search(r'https:\/\/x\.com\/i\/api\/graphql\/.*?\/UserTweets.*', req.url):
        return
    body = req.response().body()
    raw_data = json.loads(body.decode(encoding='utf-8'))

    instructions = InstructionParser(
        raw_data['data']['user']['result']['timeline']['timeline']['instructions']
    )
    threads = instructions.parse()
    for tweet in threads:
        print(f'{tweet}')
        print('-----------------')


def process(*args):
    with sync_playwright() as playwright:
        _run(playwright, *args)
