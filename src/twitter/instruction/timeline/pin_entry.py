from twitter.instruction.tweet.result import parse as ParseTweetResult


def parse(result_in: list, data: dict):
    thread = ParseTweetResult(data['entry']['content']['itemContent']['tweet_results']['result'])
    thread.pinned = True
    result_in.append(thread)
