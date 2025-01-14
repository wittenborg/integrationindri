import sqlite3
import uuid
import os
import threading
from datetime import datetime

from dbs.dslContext.ImportJobsClassDSL import ImportJobsDSL, ImportJobData
from dbs.dslContext.UserClassDSL import UserDSL, UserData
from dbs.dslContext.YouTubeKeysClassDSL import YouTubeKeysDSL
from dbs.dslContext.YouTubeKeysClassDSL import YouTubeData
from dslContext.GenericConsumersClassDSL import GenericConsumerDSL
from dslContext.GenericConsumersClassDSL import Consumer


def find_table_name(table_name, tables):
    for table in tables:
        if table_name == table[0]:
            return True
    return False

db_semaphore = threading.Semaphore(1)

class DatabaseIndri:

    def __init__(self):
        (head, tail) = os.path.split(__file__)
        path = os.path.join(head, "database.db")
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

        self.wikibase = "wikibase"
        self.miraheze = "miraheze"

        self.generic_consumer_dsl = GenericConsumerDSL(self.con, self.cur)
        self.generic_consumer_dsl.create_consumer_table(self.wikibase)
        self.generic_consumer_dsl.create_consumer_table(self.miraheze)

        self.import_jobs_dsl = ImportJobsDSL(self.con, self.cur)
        self.import_jobs_dsl.create_import_jobs_table()

        self.youtube_keys_dsl = YouTubeKeysDSL(self.con, self.cur)
        self.youtube_keys_dsl.create_youtube_key_table()

        self.user_dsl = UserDSL(self.con, self.cur)
        self.user_dsl.create_user_table()

    def set_or_update_consumer(self, wiki: str, **kwargs):
       self.generic_consumer_dsl.set_or_update_generic_consumer(wiki, **kwargs)

    def get_consumer(self, wiki: str, user_id: str) -> Consumer | None:
        return self.generic_consumer_dsl.get_generic_consumer(wiki, user_id)

    def set_request_tokens(self, wiki: str, user_id: str, request_key: str, request_secret: str) -> Consumer | None:
        params = {
            "userId": user_id,
            "requestKey": request_key,
            "requestSecret": request_secret,
        }
        return self.generic_consumer_dsl.set_or_update_generic_consumer(wiki, **params)

    def set_qs_and_access_tokens(self, wiki: str, user_id: str, qs: str, access_key: str, access_secret) -> Consumer | None:
        params = {
            "userId": user_id,
            "responseQueryString": qs,
            "accessKey": access_key,
            "accessSecret": access_secret,
        }
        return self.generic_consumer_dsl.set_or_update_generic_consumer(wiki, **params)

    def release_authentication(self, wiki: str, user_id: str):
        params = {
            "userId": user_id,
            "requestKey": None,
            "requestSecret": None,
            "responseQueryString": None,
            "accessKey": None,
            "accessSecret": None,
        }
        return self.generic_consumer_dsl.set_or_update_generic_consumer(wiki, **params)


    def create_import_job(self, user_id: str,
                      upload_size: int,
                      file_path: str) -> ImportJobData:
        return self.import_jobs_dsl.create_import_job(user_id, upload_size, file_path)

    def set_import_status(self, upload_id: str, upload_status: str):
        return self.import_jobs_dsl.update_import_job_status(upload_id, upload_status)

    def set_import_index(self, upload_id: str, upload_index: int) -> ImportJobData | None:
        return self.import_jobs_dsl.update_import_job_index(upload_id, upload_index)

    def get_import_job(self, upload_id: str) -> ImportJobData | None:
        return self.import_jobs_dsl.get_import_job(upload_id)


    def add_user(self, email: str) -> UserData:
        return self.user_dsl.add_user(email)

    def get_user(self, email: str) -> UserData:
        return self.user_dsl.get_user(email)


    def set_or_update_youtube_key(self, user_id: str, youtube_key: str) -> YouTubeData:
        return self.youtube_keys_dsl.set_or_update_youtube_key(user_id, youtube_key)

    def get_youtube_key(self, user_id: str) -> YouTubeData | None:
        return self.youtube_keys_dsl.get_youtube_key(user_id)


    def close(self):
        self.con.close()
