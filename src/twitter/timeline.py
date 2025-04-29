from datetime import datetime

from twitter.tweet import Tweet

_events = ['add_thread', 'new_thread']


class Timeline:
    _all_threads: set[Tweet] = None
    _events = {}

    _latest_post_date: datetime = None

    def __init__(self):
        self.online = set()
        self._latest_post_date = None
        for event in _events:
            self._events[event] = list()

    def _dispatch_event(self, event: str):
        for callback in self._events[event]:
            callback()

    def _should_dispatch_new_thread_event(self, tweet: Tweet):
        return self._latest_post_date and tweet.date > self._latest_post_date

    def enable_new_thread_event_since(self, date: datetime):
        self._latest_post_date = date

    def merge(self, tweets: list[Tweet]):
        for tweet in tweets:
            self.insert(tweet)

    def insert(self, tweet: Tweet):
        if tweet in self._all_threads:
            return
        self._all_threads.add(tweet)
        self._dispatch_event('add_thread')
        if self._should_dispatch_new_thread_event(tweet):
            self._dispatch_event('new_thread')

    def on(self, event: str, callback):
        if event not in _events:
            print(f'event "{event}" is invalid!')
            return
        self._events[event].append(callback)
