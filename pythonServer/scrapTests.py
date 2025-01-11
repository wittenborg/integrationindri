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

a = [1,2,3,4]

def remove_3(l):
    del l[3]

print(a)
remove_3(a)
print(a)