from datetime import datetime

from twitter.tweet import Tweet

_events = ['add_thread', 'no_more_threads']


class Timeline:
    _all_threads: set[Tweet] = None
    _current_thread: Tweet = None
    _events = {}

    _latest_post_date: datetime = None

    def __init__(self):
        self._all_threads = set()
        self._current_thread = None
        self._events = {}
        for event in _events:
            self._events[event] = list()
        self._latest_post_date = None

        self._enable_event_log()

    def _enable_event_log(self):
        def gen_desc(tweet: Tweet):
            max_length = 50
            draft = str(tweet).replace('\n', '')
            if len(draft) <= max_length:
                return draft
            else:
                return draft[:max_length] + '...'

        async def on_add_thread(tweet: Tweet, new: bool):
            print(f'\revent: add_thread, {new and "[NEW] " or ""}{gen_desc(tweet)}')

        async def on_no_more_threads():
            print('event: no_more_threads')

        self.on('add_thread', on_add_thread)
        self.on('no_more_threads', on_no_more_threads)

    async def _dispatch_event(self, event: str):
        async def send(*args):
            for callback in self._events[event]:
                await callback(*args)

        match event:
            case 'add_thread':
                await send(self._current_thread, self._should_dispatch_new_thread_event())
            case 'no_more_threads':
                await send()

    def _should_dispatch_new_thread_event(self):
        return self._latest_post_date and self._current_thread.date > self._latest_post_date

    def enable_new_thread_event_since(self, date: datetime):
        self._latest_post_date = date

    async def insert(self, tweet: Tweet):
        if tweet in self._all_threads:
            return
        self._all_threads.add(tweet)
        self._current_thread = tweet
        await self._dispatch_event('add_thread')

    async def trigger_no_more_threads(self):
        await self._dispatch_event('no_more_threads')

    async def trigger_add_thread(self, thread: Tweet, new: bool):
        if thread not in self._all_threads:
            return
        for callback in self._events['add_thread']:
            await callback(thread, new)

    def on(self, event: str, callback):
        if event not in _events:
            print(f'event "{event}" is invalid!')
            return
        self._events[event].append(callback)
