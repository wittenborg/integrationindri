from mwoauth import ConsumerToken, Handshaker
from requests_oauthlib import OAuth1
import requests

# Connect To Express Server via STATIC NGROK 10a v3
consumer_key = "cd010723955ab90f5e10ae507660b920"
consumer_secret = "de13fada4c4b6d38adfd7e9b996916675a89d18b"

wiki = "https://bnwiki.wikibase.cloud/w/index.php"

consumer = ConsumerToken(consumer_key, consumer_secret)
print("consumer:", consumer)

# Construct handshaker with wiki URI and consumer
handshaker = Handshaker(wiki, consumer)
print("handshaker: ", handshaker)

# Step 1: Initialize -- ask MediaWiki for a temporary key/secret for user
redirect, request_token = handshaker.initiate()
print("Redirect: ", redirect, "Request_Token: ", request_token)

# Step 2: Authorize -- send user to MediaWiki to confirm authorization
print("Point your browser to: %s" % redirect)  #
response_qs = input("Response query string: ")

# Step 3: Complete -- obtain authorized key/secret for "resource owner"
access_token = handshaker.complete(request_token, response_qs)
print(str(access_token))

# Construct an auth object with the consumer and access tokens
auth1 = OAuth1(consumer_key,
               client_secret=consumer_secret,
               resource_owner_key=access_token.key,
               resource_owner_secret=access_token.secret)

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

print("doc:", doc)