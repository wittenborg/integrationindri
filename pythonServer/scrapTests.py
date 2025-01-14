import json

data = {
    "labels": {
        "en": {
            "language": "en",
            "value": "Wie wir in Zukunft WIRKLICH Energie erzeugen werden | Energie-Doku 2025"
        }
    }
}

json_object = str(json.dumps(data))
print(type(str(json_object)))

data1 = {"hello": "world2"}
data2 = {"hello": "world2"}
data3 = {"hello": "world3", **data1, **data2}
print(data3)
