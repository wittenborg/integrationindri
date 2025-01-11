import json
import os
import pickle


class FileDB:
    def __init__(self, user_id: str):
        (head, tail) = os.path.split(__file__)
        self.path_json = os.path.join(head, f"{user_id}.json")
        self.path_pkl = os.path.join(head, f"{user_id}.pkl")

    def upload(self, data) -> None:
        with open(self.path_json, "w") as file:
            json.dump(data, file)

    def read(self):
        with open(self.path_json, 'r', encoding='utf-8') as file:
            return json.load(file)


    def upload_pickle(self, obj) -> None:
        with open(self.path_pkl, 'wb') as file:
            pickle.dump(obj, file, pickle.HIGHEST_PROTOCOL)

    def read_pickle(self):
        with open(self.path_pkl, 'rb') as inp:
            return pickle.load(inp)

    def delete_pickle(self):
        os.remove(self.path_pkl)

if __name__ == "__main__":
    fileDB = FileDB("213-4324sadfsd23-23edsa")

    data = [{
    "labels": {
        "en": {
            "language": "en",
            "value": "Wie wir in Zukunft WIRKLICH Energie erzeugen werden | Energie-Doku 2025"
        }
    }
}]

    fileDB.upload(data)

    rdata = fileDB.read()
    print(rdata)