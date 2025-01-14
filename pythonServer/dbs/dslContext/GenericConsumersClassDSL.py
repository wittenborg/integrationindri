import os
import sqlite3

from dbs.DBSIndri import findTableName


class Consumer:
    def __init__(self,
                 user_id: str,
                 consumer_key: str | None,
                 consumer_secret: str | None,
                 request_key: str | None,
                 request_secret: str | None,
                 response_query_string: str | None,
                 access_key: str | None,
                 access_secret: str | None, ):
        self.user_id = user_id
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.request_key = request_key
        self.request_secret = request_secret
        self.response_query_string = response_query_string
        self.access_key = access_key
        self.access_secret = access_secret


class GenericConsumerDSL:

    def __init__(self, con, cur):
        self.con = con
        self.cur = cur

    def create_consumer_table(self, table_name):
        params = {"tableName": table_name}
        tables = self.cur.execute("SELECT name FROM sqlite_master").fetchall()
        if not findTableName(table_name, tables):
            self.cur.execute("""
                        CREATE TABLE :tableName (
                        userId VARCHAR(255) NOT NULL PRIMARY KEY,
                        consumerKey VARCHAR(255),
                        consumerSecret VARCHAR(255),
                        requestKey VARCHAR(255),
                        requestSecret VARCHAR(255),
                        responseQueryString VARCHAR(1023),
                        accessKey VARCHAR(255),
                        accessSecret VARCHAR(255)
                    )
                    """, params)
            self.con.commit()

    def set_or_update_generic_consumer(self, table_name, **kwargs) -> Consumer:
        consumer = self.get_generic_consumer(table_name, kwargs["user_id"])
        params = {"tableName": table_name,
                  "userId": kwargs["user_id"],
                  "consumerKey": consumer.consumer_key,
                  "consumerSecret": consumer.consumer_secret,
                  "requestKey": consumer.request_key,
                  "requestSecret": consumer.request_secret,
                  "responseQueryString": consumer.response_query_string,
                  "accessKey": consumer.access_key,
                  "accessSecret": consumer.access_secret,
                  **kwargs}
        if consumer is None:
            self.cur.execute(
                f"""
                        INSERT INTO :table (userId, consumerKey, consumerSecret, requestKey, requestSecret, responseQueryString, accessKey, accessSecret) 
                        VALUES (:userId, :consumerKey, :consumerSecret, :requestKey, :requestSecret, :responseQueryString, :accessKey, :accessSecret)        
                        """, params)
        else:
            self.cur.execute(
                f"""
                    UPDATE :tableName 
                    SET consumerKey = :consumerKey, consumerSecret = :consumerSecret, requestKey = :requestKey, requestSecret = :requestSecret, responseQueryString = :responseQueryString, accessKey = :accessKey, accessSecret = :accessSecret
                    WHERE userId = :userId
                    """, params)
        self.con.commit()
        return self.get_generic_consumer(table_name, kwargs["user_id"])

    def get_generic_consumer(self, table_name, user_id) -> Consumer | None:
        params = {"userId": user_id, "tableName": table_name}
        result = self.cur.execute(
            f"""
                        SELECT userId, consumerKey, consumerSecret, requestKey, requestSecret, responseQueryString, accessKey, accessSecret
                        FROM :tableName
                        WHERE userId = :userId
                    """, params).fetchone()
        if result is not None:
            return Consumer(
                user_id=result[0],
                consumer_key=result[1],
                consumer_secret=result[2],
                request_key=result[3],
                request_secret=result[4],
                response_query_string=result[5],
                access_key=result[6],
                access_secret=result[7]
            )
        else:
            return None
