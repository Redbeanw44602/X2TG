from datetime import datetime

from twitter.config import MAIN_URL, FXTWITTER_URL, ENABLE_FXTWITTER


class Tweet:
    author = None  # todo
    text: str = ''
    photos: list[str] = []
    pinned: bool = False
    reposted_href: str = None
    date: datetime = None
    rest_id: int = 0

    def __init__(self):
        self.author = None
        self.text = ''
        self.photos = []
        self.pinned = False
        self.reposted_href = None
        self.date = None
        self.rest_id = 0

    def __eq__(self, value):
        return isinstance(self, Tweet) and self.rest_id == value.rest_id

    def __hash__(self):
        return self.rest_id

    def set_reposted(self, username: str, rest_id: str):
        base_url = ENABLE_FXTWITTER and FXTWITTER_URL or MAIN_URL
        self.reposted_href = f'{base_url}/{username}/status/{rest_id}'

    def set_date(self, date: str):
        """
        Wed Apr 23 00:00:00 +0000 2025
        """
        self.date = datetime.strptime(date, '%a %b %d %H:%M:%S %z %Y')

    def __str__(self):
        if self.reposted_href:
            return f'(Reposted) {self.reposted_href}'
        result = len(self.text) == 0 and '(Empty)' or self.text
        if self.pinned:
            result += '\n+ (Pinned)'
        for photo in self.photos:
            result += f'\n+ {photo}'
        return result
