from twitter.instruction.tweet.result import parse as ParseTweetResult


def parse(result_in: list, data: dict):
    for entry in data['entries']:
        if 'itemContent' in entry['content']:
            content = entry['content']['itemContent']
            assert content['itemType'] == 'TimelineTweet', 'unsupported.'

            thread = ParseTweetResult(content['tweet_results']['result'])
            result_in.append(thread)
