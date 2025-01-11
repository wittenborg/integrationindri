from mwoauth import ConsumerToken, complete, identify, initiate, RequestToken
from requests_oauthlib import OAuth1
import requests
import json

wiki = "https://bnwiki.wikibase.cloud/w/index.php"

def get_authentication_link(consumer_key: str, consumer_secret: str) -> tuple[str, str, str]:
    consumer_token = ConsumerToken(consumer_key, consumer_secret)
    redirect, request_token = initiate(wiki, consumer_token)
    return redirect, request_token.key, request_token.secret


def get_access_token(
        consumer_key: str,
        consumer_secret: str,
        request_key: str,
        request_secret: str,
        response_qs: str
):
    consumer_token = ConsumerToken(consumer_key, consumer_secret)
    request_token = RequestToken(request_key, request_secret)
    access_token = complete(wiki, consumer_token, request_token, response_qs)
    return access_token.key, access_token.secret


def get_csrf_token(
        o_auth: OAuth1
):
    response = requests.get(
        "https://bnwiki.wikibase.cloud/w/api.php",
        params={
            'action': "query",
            'format': "json",
            'meta': "tokens",
        },
        auth=o_auth
    )
    doc = response.json()
    print("csrf:", doc["query"]["tokens"]["csrftoken"])
    return doc["query"]["tokens"]["csrftoken"]