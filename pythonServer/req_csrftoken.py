from requests_oauthlib import OAuth1
import requests
import json

consumer_key = "cd010723955ab90f5e10ae507660b920"
consumer_secret = "de13fada4c4b6d38adfd7e9b996916675a89d18b"
access_token_key = "5304860666ecc93fd373e6ed65947173"
access_token_secret = "cf4e14fd12d17b83757cf5e9857d42ce4fdb9ca5"

wiki = "https://bnwiki.wikibase.cloud/w/index.php"

auth1 = OAuth1(consumer_key,
               client_secret=consumer_secret,
               resource_owner_key=access_token_key,
               resource_owner_secret=access_token_secret)

response = requests.get(
    "https://bnwiki.wikibase.cloud/w/api.php",
    params={
        'action': "query",
        'format': "json",
        'meta': "tokens",
    },
    auth=auth1
)
doc = response.json()

print("csrf:", doc["query"]["tokens"]["csrftoken"])

csrf_token = doc["query"]["tokens"]["csrftoken"]
data = {
    "labels": {
        "en": {
            "language": "en",
            "value": "Wie schädlich ist die Pille wirklich?"
        }
    }
}

response = requests.post(
    "https://bnwiki.wikibase.cloud/w/api.php",
    params={
        'action': "wbeditentity",
        'format': "json",
        'new': 'item',

        'data': str(json.dumps(data)),
    },
    data={
    'token': csrf_token,
    },
    auth=auth1
)

doc = response.json()

print("doc:", doc)

