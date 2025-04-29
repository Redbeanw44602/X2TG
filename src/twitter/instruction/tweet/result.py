from twitter.tweet import Tweet
from twitter.config import MAIN_URL


def parse(data: dict) -> Tweet:
    thread = Tweet()

    legacy_data = data['legacy']

    full_text: str = legacy_data['full_text']
    rich_entities = legacy_data['entities']

    # is reposted?
    if 'retweeted_status_result' in legacy_data:
        status = legacy_data['retweeted_status_result']  # TODO: separate it.
        username = status['result']['core']['user_results']['result']['legacy']['screen_name']
        rest_id = status['result']['rest_id']
        thread.set_reposted(username, rest_id)
        return thread

    # convert @user -> [@user](https://x.com/user)
    mentions = rich_entities['user_mentions']
    for mention in mentions:
        username = mention['screen_name']
        full_text = full_text.replace(f'@{username}', f'[@{username}]({MAIN_URL}/{username})')

    # handle images
    if 'media' in rich_entities:
        medias = rich_entities['media']
        for media in medias:
            full_text = full_text.replace(media['url'], '')
            thread.photos.append(media['media_url_https'])

    thread.set_date(legacy_data['created_at'])
    thread.rest_id = int(data['rest_id'])
    thread.text = full_text.strip()
    return thread
