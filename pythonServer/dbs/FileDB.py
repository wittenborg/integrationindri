import json
import os
import pickle


class FileDB:
    def __init__(self, *argv):
        (head, tail) = os.path.split(__file__)
        if len(argv) > 1:
            t = os.path.join(argv[0], *(argv[1:]))
            self.path_json = os.path.join(head, f"{t}.json")
            self.path_pkl = os.path.join(head, f"{t}.pkl")
        elif len(argv) == 1:
            self.path_json = os.path.join(head, f"{argv[0]}.json")
            self.path_pkl = os.path.join(head, f"{argv[0]}.pkl")
        else:
            self.path_json = None


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