import requests
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import sys

def get_youtube_video_data(api_key: str, watch_ids: list[str]):
    if len(watch_ids) < 50:
        response = requests.get(
            "https://youtube.googleapis.com/youtube/v3/videos",
            params={
                "key": api_key,
                "part": ["snippet", "contentDetails"],
                "id": watch_ids
            }
        )
        return response.json()
    else:
        return None

endpoint_url = "https://bnwiki.wikibase.cloud/query/sparql"
def wikibase_query_service_request(query):
    response = requests.post(endpoint_url,
                             data={"query": query},
                             headers={"Accept": "application/sparql-results+json"})
    return response.json()


# check for video itself
def video_exists(urls: list[str]):
    urls_concat = " ".join(list(map(lambda u: f"<{u}>", urls)))
    query = """PREFIX propt: <https://bnwiki.wikibase.cloud/prop/direct/>
    PREFIX item: <https://bnwiki.wikibase.cloud/entity/>
    PREFIX prop: <https://bnwiki.wikibase.cloud/prop/>
    PREFIX pqual: <https://bnwiki.wikibase.cloud/prop/qualifier/>
    PREFIX pstat: <https://bnwiki.wikibase.cloud/prop/statement/>
    
    SELECT ?media ?url
    WHERE {
      VALUES ?url { """ + urls_concat + """ }
      ?media propt:P1 item:Q4 ;
             prop:P10 / pstat:P10 ?url .
    }"""
    results = wikibase_query_service_request(query)

    dict_results = dict()
    for url in urls:
        dict_results[url] = None

    for url in results["results"]["bindings"]:
        dict_results[url["url"]["value"]] = url["media"]["value"]
    # print(dict_results)
    return dict_results


def channel_exists(channel_ids: list[str]):
    query = """
    PREFIX propt: <https://bnwiki.wikibase.cloud/prop/direct/>
    PREFIX item: <https://bnwiki.wikibase.cloud/entity/>
    PREFIX prop: <https://bnwiki.wikibase.cloud/prop/>
    PREFIX pqual: <https://bnwiki.wikibase.cloud/prop/qualifier/>
    PREFIX pstat: <https://bnwiki.wikibase.cloud/prop/statement/>
    
    SELECT ?channel ?channelId
    WHERE {
      VALUES ?channelId { """ + "".join(map(lambda id: "\"" + id + "\"",channel_ids)) + """}
      ?channel propt:P1 item:Q3 ;
               propt:P30 ?channelId .
    }
    """
    results = wikibase_query_service_request(query)

    dict_results = dict()
    for channel in channel_ids:
        dict_results[channel] = None
    for channel in results["results"]["bindings"]:
        dict_results[channel["channelId"]["value"]] = channel["channel"]["value"]

    # print(dict_results)
    return dict_results

def category_exists(categories: list[str]):
    query = """
    PREFIX propt: <https://bnwiki.wikibase.cloud/prop/direct/>
    PREFIX item: <https://bnwiki.wikibase.cloud/entity/>
    PREFIX prop: <https://bnwiki.wikibase.cloud/prop/>
    PREFIX pqual: <https://bnwiki.wikibase.cloud/prop/qualifier/>
    PREFIX pstat: <https://bnwiki.wikibase.cloud/prop/statement/>
    
    SELECT ?category ?categoryName
    WHERE {
      VALUES ?categoryName { """ + " ".join(list(map(lambda c: f"\"{c}\"@en", categories))) + """ }
      ?category propt:P1 item:Q10 ;
             rdfs:label ?categoryName .
    }
    """
    #print(query)
    results = wikibase_query_service_request(query)

    dict_results = dict()
    for value in categories:
        dict_results[value] = None
    for category in results["results"]["bindings"]:
        dict_results[category["categoryName"]["value"]] = category["category"]["value"]

    # print(dict_results)
    return dict_results


def create_new_item(data, o_auth1, token):
    response = requests.post(
        "https://bnwiki.wikibase.cloud/w/api.php",
        params={
            'action': "wbeditentity",
            'format': "json",
            'new': 'item',

            'data': str(json.dumps(data)),
        },
        data={
            'token': token,
        },
        auth=o_auth1
    )
    return response.json()

if __name__ == "__main__":
    """
    res = category_exists([])
    print(res)
    res = channel_exists(["UCesjlAoEgN_Sz_cKTvKEmmw", "asdasd"])
    print(res)
    res = video_exists(["https://www.youtube.com/watch?v=FuV3ysSKOsw", "https://www.youtube.com/watch?v=nVm_arH33F0", "https://www.youtube.com/watch?v=Fasdweaacx"])
    print(res)

    """
    api_key = "AIzaSyBDb9q9lMnzeIbNauMLhCN2Gn1HHITRxo4"
    watch_ids = ["fAMktPJVILw", "0XON4wIvkAM"]
    res = get_youtube_video_data(api_key, watch_ids)
    print(json.dumps(res))

