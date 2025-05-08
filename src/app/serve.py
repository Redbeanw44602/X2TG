import re
import os
import asyncio
import json
import random
from datetime import datetime, timezone, timedelta

from playwright.async_api import async_playwright, Playwright, Request, Page
from telegram import Bot, InputMediaPhoto, Message
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler

import telegraph.ping as PingCommand
import telegraph.link as LinkCommand
import telegraph.show as ShowCommand
import telegraph.fixtl as FixTlCommand

from twitter.instruction.parser import InstructionParser
from twitter.tweet import Tweet
from twitter.timeline import Timeline
from twitter.config import MAIN_URL

_page: Page = None
_timeline: Timeline = None

_bot: Bot = None
_bot_app: Application = None
_chat_id: int = None

_run_fake_browsing = asyncio.Event()

# TODO: remove it.
_has_more_threads = asyncio.Event()

# TODO: remove it.
data = {}
status = {'event': 'Initializing'}
_username = ''


def _update(stat: str, data=None):
    print(f'update state: {stat}')
    status['event'] = stat
    status['data'] = data


async def _run(
    playwright: Playwright, browser_context: str, browser_kind: str, username: str, headless: bool
):
    global _page, _username
    _username = username

    browser = await getattr(playwright, browser_kind).launch(headless=headless)
    context = await browser.new_context(storage_state=browser_context)
    print('browser context has been restored.')

    # home page
    _page = await context.new_page()
    _page.on('request', _on_request)

    print('waiting for the page to load... (timeout: 30s)')
    await _page.goto(f'{MAIN_URL}/{username}')

    try:
        avatar_frame = _page.get_by_test_id('SideNav_AccountSwitcher_Button')
        assert await avatar_frame.count() != 0, 'login expired.'

        print('waiting for the tweets to load... (timeout: 30s)')
        await _page.get_by_test_id('tweet').first.wait_for()

        # start service

        print('starting fake browsing task...')
        fake_browse_task = asyncio.create_task(_fake_browsing())
        _run_fake_browsing.set()

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
            case 'test telegram':
                await _bot.send_message(chat_id=_chat_id, text='Hello world!\n\n#X2TG_TEST')
                print('test message sent.')
            case 'sync all':
                await _run_sync_all()
            case _:
                print('Please type "quit" to exit.')


async def _scroll_to(position: int):
    await _page.evaluate(f"""
        window.scrollTo({{ top: {position}, behavior: 'smooth' }});
    """)


async def _scroll_bottom():
    await _page.evaluate("""
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    """)


async def _run_sync_all():
    _update('Syncing')

    _run_fake_browsing.clear()
    _has_more_threads.set()

    print('trying to sync all tweets...')
    while _has_more_threads.is_set():
        await _scroll_bottom()
        await asyncio.sleep(2)

    print('all thread have been pulled.')

    _has_more_threads.clear()
    _run_fake_browsing.set()


async def _fake_browsing():
    async def _scroll_check(*args):
        await _run_fake_browsing.wait()  # TODO: better way to do this.
        await _scroll_to(*args)

    while True:
        scroll_y_0 = random.randint(2000, 4000)
        scroll_wait_0 = random.randint(8, 15)
        scroll_y_1 = random.randint(0, 100)
        scroll_wait_1 = random.randint(2, 8) * 60
        print(
            f'\rrunjob: fake browsing... ({scroll_y_0}, {scroll_wait_0}s) ({scroll_y_1}, {scroll_wait_1}s)'
        )
        _update('Browsing')
        await _scroll_check(scroll_y_0)
        await asyncio.sleep(scroll_wait_0)
        await _scroll_check(scroll_y_1)
        _update('Resting', datetime.now() + timedelta(seconds=scroll_wait_1))
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

    is_empty = True
    for tweet in tweets:
        if not tweet.pinned:
            is_empty = False
            await _timeline.insert(tweet)

    if is_empty:
        await _timeline.trigger_no_more_threads()


def _load_forwarded_message():
    global data

    if not os.path.isfile('data.json'):
        return
    with open('data.json') as file:
        data = json.loads(file.read())


def store_forwarded_message(rest_id: int, messages: list[Message]):
    data[rest_id] = []
    for message in messages:
        data[rest_id].append(message.message_id)
    with open('data.json', 'w') as file:
        file.write(json.dumps(data))


async def _on_add_thread(tweet: Tweet, new: bool):
    if not new:
        return
    messages = []
    message = None
    if tweet.reposted_href:
        print(tweet.reposted_href)
        message = await _bot.send_message(
            chat_id=_chat_id,
            text=tweet.reposted_href,
            disable_web_page_preview=not tweet.reposted_href,
        )
    elif not tweet.photos:
        message = await _bot.send_message(
            chat_id=_chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=tweet.text,
            disable_web_page_preview=not tweet.reposted_href,
        )
    elif len(tweet.photos) == 1:
        message = await _bot.send_photo(
            chat_id=_chat_id,
            parse_mode=ParseMode.MARKDOWN,
            photo=tweet.photos[0],
            caption=tweet.text,
        )
    elif len(tweet.photos) > 1:
        media = []
        for photo in tweet.photos:
            media.append(InputMediaPhoto(media=photo))
        messages = list(
            await _bot.send_media_group(
                chat_id=_chat_id, parse_mode=ParseMode.MARKDOWN, media=media, caption=tweet.text
            )
        )
    if message:
        messages.append(message)
    store_forwarded_message(tweet.rest_id, messages)


async def _on_no_more_threads():
    _has_more_threads.clear()


async def process(**kwargs):
    global _timeline
    global _bot
    global _chat_id

    _load_forwarded_message()

    _timeline = Timeline()
    _timeline.on('add_thread', _on_add_thread)
    _timeline.on('no_more_threads', _on_no_more_threads)
    _timeline.enable_new_thread_event_since(datetime.now(timezone.utc))

    _bot = Bot(token=kwargs['bot_token'])
    _chat_id = kwargs['chat_id']
    assert _chat_id < 0

    _bot_app = ApplicationBuilder().token(token=kwargs['bot_token']).build()
    _bot_app.add_handler(CommandHandler('ping', PingCommand.handle))
    _bot_app.add_handler(CommandHandler('link', LinkCommand.handle))
    _bot_app.add_handler(CommandHandler('show', ShowCommand.handle))
    # _bot_app.add_handler(CommandHandler('fixtl', FixTlCommand.hanele))
    # _bot_app.add_handler(CallbackQueryHandler(FixTlCommand.handle_callback))

    await _bot_app.initialize()
    await _bot_app.start()
    await _bot_app.updater.start_polling()

    kwargs.pop('bot_token')
    kwargs.pop('chat_id')

    async with async_playwright() as playwright:
        await _run(playwright, **kwargs)
