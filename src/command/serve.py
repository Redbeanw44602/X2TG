import re
import asyncio
import json
import random
from datetime import datetime, timezone

from playwright.async_api import async_playwright, Playwright, Request, Page
from telegram import Bot, InputMediaPhoto
from telegram.constants import ParseMode

from twitter.instruction.parser import InstructionParser
from twitter.tweet import Tweet
from twitter.timeline import Timeline
from twitter.config import MAIN_URL


_timeline: Timeline = None

_bot: Bot = None
_chat_id: int = None


async def _run(
    playwright: Playwright, browser_context: str, browser_kind: str, username: str, headless: bool
):
    browser = await getattr(playwright, browser_kind).launch(headless=headless)
    context = await browser.new_context(storage_state=browser_context)
    print('browser context has been restored.')

    # home page
    page = await context.new_page()
    page.on('request', _on_request)

    print('waiting for the page to load... (timeout: 30s)')
    await page.goto(f'{MAIN_URL}/{username}')

    try:
        avatar_frame = page.get_by_test_id('SideNav_AccountSwitcher_Button')
        assert await avatar_frame.count() != 0, 'login expired.'

        print('waiting for the tweets to load... (timeout: 30s)')
        await page.get_by_test_id('tweet').first.wait_for()

        # start service

        print('starting fake browsing task...')
        fake_browse_task = asyncio.create_task(_fake_browsing(page))

        print('starting console input handler...')
        input_task = asyncio.create_task(_console_input())

        await input_task
        fake_browse_task.cancel()

    except Exception as e:
        raise e  # TODO: for debug only

    await context.storage_state(path=browser_context)
    await context.close()
    await browser.close()


async def _console_input():
    Exited = False

    while not Exited:
        cmd = await asyncio.to_thread(input, '> ')
        match cmd:
            case 'q' | 'quit' | 'exit':
                Exited = True
            case _:
                print('Please type "quit" to exit.')


async def _scroll_to(page: Page, position: int):
    await page.evaluate(f"""
        window.scrollTo({{ top: {position}, behavior: 'smooth' }});
    """)


async def _fake_browsing(page: Page):
    while True:
        scroll_y_0 = random.randint(2000, 4000)
        scroll_wait_0 = random.randint(8, 15)
        scroll_y_1 = random.randint(0, 100)
        scroll_wait_1 = random.randint(2, 8) * 60
        print(
            f'\rrunjob: fake browsing... ({scroll_y_0}, {scroll_wait_0}s) ({scroll_y_1}, {scroll_wait_1}s)'
        )
        await _scroll_to(page, scroll_y_0)
        await asyncio.sleep(scroll_wait_0)
        await _scroll_to(page, scroll_y_1)
        await asyncio.sleep(scroll_wait_1)


async def _on_request(req: Request):
    if not re.search(r'\/i\/api\/graphql\/.*?\/UserTweets.*', req.url):
        return
    response = await req.response()
    body = await response.body()
    raw_data = json.loads(body.decode(encoding='utf-8'))

    instructions = raw_data['data']['user']['result']['timeline']['timeline']['instructions']

    tweets = InstructionParser(instructions).parse()
    tweets.reverse()

    for tweet in tweets:
        if not tweet.pinned:
            await _timeline.insert(tweet)


async def _on_new_thread(tweet: Tweet):
    def gen_desc():
        max_length = 50
        draft = str(tweet).replace('\n', '')
        if len(draft) <= max_length:
            return draft
        else:
            return draft[:max_length] + '...'

    print(f'\revent: new_thread, {gen_desc()}')
    if tweet.reposted_href:
        await _bot.send_message(
            chat_id=_chat_id, parse_mode=ParseMode.MARKDOWN, text=tweet.reposted_href
        )
        return
    if not tweet.photos:
        await _bot.send_message(chat_id=_chat_id, parse_mode=ParseMode.MARKDOWN, text=tweet.text)
    elif len(tweet.photos) == 1:
        await _bot.send_photo(
            chat_id=_chat_id,
            parse_mode=ParseMode.MARKDOWN,
            photo=tweet.photos[0],
            caption=tweet.text,
        )
    elif len(tweet.photos) > 1:
        media = []
        for photo in tweet.photos:
            media.append(InputMediaPhoto(media=photo))
        await _bot.send_media_group(
            chat_id=_chat_id, parse_mode=ParseMode.MARKDOWN, media=media, caption=tweet.text
        )


async def process(**kwargs):
    global _timeline
    global _bot
    global _chat_id

    _timeline = Timeline()
    _timeline.on('new_thread', _on_new_thread)
    _timeline.enable_new_thread_event_since(datetime.now(timezone.utc))

    _bot = Bot(token=kwargs['bot_token'])
    _chat_id = kwargs['chat_id']

    kwargs.pop('bot_token')
    kwargs.pop('chat_id')

    async with async_playwright() as playwright:
        await _run(playwright, **kwargs)
