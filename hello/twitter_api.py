import os
import base64
import json
import sys
try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request, HTTPError


API_ENDPOINT = 'https://api.twitter.com'
API_VERSION = '1.1'
REQUEST_TOKEN_URL = '%s/oauth2/token' % API_ENDPOINT
# REQUEST_RATE_LIMIT = '%s/%s/application/rate_limit_status.json' % \
#                      (API_ENDPOINT, API_VERSION)
SEARCH_ENDPOINT = 'https://api.twitter.com/1.1/search/tweets.json?q=%23{}'

key = os.environ.get('CONSUMER_KEY')
secret = os.environ.get('CONSUMER_SECRET')


class ClientException(Exception):
    """Error."""

    pass


class Client(object):
    """Handle application only auth."""

    def __init__(self, consumer_key, consumer_secret):
        """Initialize."""
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = ''

    def request(self, url):
        """Process the requested api url."""
        if not self.access_token:
            self.access_token = self._get_access_token()

        request = Request(url)
        request.add_header('Authorization', 'Bearer %s' % self.access_token)
        try:
            response = urlopen(request)
        except HTTPError:
            raise ClientException

        raw_data = response.read().decode('utf-8')
        data = json.loads(raw_data)
        return data['statuses']

    def _get_access_token(self):
        """Establish the bearer tolken and get data."""
        bearer_token = '%s:%s' % (self.consumer_key, self.consumer_secret)
        encode_bearer_token = base64.b64encode(bearer_token.encode('ascii'))
        request = Request(REQUEST_TOKEN_URL)
        request.add_header('Content-Type',
                           'application/x-www-form-urlencoded;charset=UTF-8')
        request.add_header('Authorization',
                           'Basic %s' % encode_bearer_token.decode('utf-8'))
        request_data = 'grant_type=client_credentials'.encode('ascii')

        if sys.version_info < (3, 4):
            request.add_data(request_data)
        else:
            request.data = request_data

        response = urlopen(request)
        raw_data = response.read().decode('utf-8')
        data = json.loads(raw_data)
        return data['access_token']


def get_twitter_comments(ticker):
    client = Client(key, secret)
    resp = client.request(SEARCH_ENDPOINT.format(ticker))
    return resp


def json_into_table(message, ticker):
    if not isinstance(ticker, str):
        raise ValueError("Invalid ticker :(")
    try:
        to_return = {
            "social_id": message['id'],
            "focus": ticker,
            "popularity": message['favorite_count'],
            "author": message['user']['name'],
            "author_image": message['user']['profile_image_url'],
            "created_time": message['created_at'],
            "content": message['text'],
            "symbols": [stock['symbol'] for stock in message['entities']['symbols']],
            "hashtags": [hashtag['text'] for hashtag in message['entities']['hashtags']],
            "urls": [url['url'] for url in message['entities']['urls']],
        }
        return to_return
    except (TypeError, KeyError):
        raise ValueError("Invalid message")


if __name__ == "__main__":
    ticker = "MSFT"
    messages = get_twitter_comments(ticker)
    for index, message in enumerate(messages):
        message = json_into_table(message, ticker)
        messages[index] = message