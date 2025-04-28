from twitter.config import MAIN_URL, FXTWITTER_URL, ENABLE_FXTWITTER


class Tweet:
    author = None  # todo
    text: str = ''
    photos: list[str] = []
    pinned: bool = False
    reposted_href = None

    def __init__(self):
        self.author = None
        self.text = ''
        self.photos = []
        self.pinned = False
        self.reposted_href = None

    def set_text(self, text: str):
        self.text = text

    def add_photo(self, url: str):
        self.photos.append(url)

    def set_pinned(self, val: bool):
        self.pinned = val

    def set_reposted(self, username: str, rest_id: str):
        base_url = ENABLE_FXTWITTER and FXTWITTER_URL or MAIN_URL
        self.reposted_href = f'{base_url}/{username}/status/{rest_id}'

    def __str__(self):
        if self.reposted_href:
            return f'(Reposted) {self.reposted_href}'
        result = self.text
        if self.pinned:
            result += '\n+ (Pinned)'
        for photo in self.photos:
            result += f'\n+ {photo}'
        return result
