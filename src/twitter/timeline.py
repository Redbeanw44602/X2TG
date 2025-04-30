from datetime import datetime

from twitter.tweet import Tweet

_events = ['add_thread', 'new_thread']


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

    async def _dispatch_event(self, event: str):
        if event == 'new_thread':
            if not self._should_dispatch_new_thread_event():
                return
        for callback in self._events[event]:
            await callback(self._current_thread)

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
        await self._dispatch_event('new_thread')

    def on(self, event: str, callback):
        if event not in _events:
            print(f'event "{event}" is invalid!')
            return
        self._events[event].append(callback)
