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
_chat_id: str = None


async def _run(
    playwright: Playwright, browser_context: str, username: str, bot_token: str, chat_id: str
):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(storage_state=browser_context)
    print('context has been restored.')

    # home page
    page = await context.new_page()
    page.on('request', _on_request)

    await page.goto(f'{MAIN_URL}/{username}')

    try:
        avatar_frame = page.get_by_test_id('SideNav_AccountSwitcher_Button')
        assert await avatar_frame.count() != 0, 'login expired.'

        # wait for tweets
        await page.get_by_test_id('tweet').first.wait_for(timeout=30 * 1000)

        # start service
        fake_browse_task = asyncio.create_task(_fake_browsing(page))
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
        cmd = await asyncio.to_thread(input, '>>> ')
        match cmd:
            case 'q' | 'quit' | 'exit':
                Exited = True
            case _:
                print('Use "quit" to exit the service.')


async def _scroll_to(page: Page, position: int):
    await page.evaluate(f"""
        window.scrollTo({{ top: {position}, behavior: 'smooth' }});
    """)


async def _fake_browsing(page: Page):
    while True:
        await _scroll_to(page, random.randint(2000, 4000))
        await asyncio.sleep(random.randint(8, 15))
        await _scroll_to(page, random.randint(0, 100))
        await asyncio.sleep(random.randint(2, 8) * 60)


async def _on_request(req: Request):
    if not re.search(r'\/i\/api\/graphql\/.*?\/UserTweets.*', req.url):
        return
    response = await req.response()
    body = await response.body()
    raw_data = json.loads(body.decode(encoding='utf-8'))

    instructions = raw_data['data']['user']['result']['timeline']['timeline']['instructions']

    tweets = InstructionParser(instructions).parse()

    await _timeline.merge(tweets)


async def _on_new_thread(tweet: Tweet):
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

    async with async_playwright() as playwright:
        await _run(playwright, **kwargs)
