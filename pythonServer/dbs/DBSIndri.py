import sqlite3
import uuid
import os
import threading


def findTableName(tableName, tables):
    for table in tables:
        if tableName == table[0]:
            return True
    return False


db_semaphore = threading.Semaphore(1)


class Consumer:
    def __init__(self,
                 user_id: str,
                 consumer_key: str | None,
                 consumer_secret: str | None,
                 request_key: str | None,
                 request_secret: str | None,
                 response_query_string: str | None,
                 access_key: str | None,
                 access_secret: str | None,
                 upload_index: int | None,
                 upload_status: bool | None,):
        self.user_id = user_id
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.request_key = request_key
        self.request_secret = request_secret
        self.response_query_string = response_query_string
        self.access_key = access_key
        self.access_secret = access_secret
        self.upload_index = upload_index
        self.upload_status = upload_status


class DatabaseIndri:

    def __init__(self):
        (head, tail) = os.path.split(__file__)
        path = os.path.join(head, "database.db")
        print("Initializing Database Indri:", path, "__file__:", __file__)
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()
        self.tables = self.cur.execute("SELECT name FROM sqlite_master").fetchall()
        if not findTableName("Consumers", self.tables):
            self.cur.execute("""
                CREATE TABLE Consumers (
                userId VARCHAR(255) NOT NULL PRIMARY KEY,
                consumerKey VARCHAR(255),
                consumerSecret VARCHAR(255),
                requestKey VARCHAR(255),
                requestSecret VARCHAR(255),
                responseQueryString VARCHAR(1023),
                accessKey VARCHAR(255),
                accessSecret VARCHAR(255),
                uploadIndex INTEGER,
                uploadFinished BOOLEAN
            )
            """)
            self.con.commit()
        if not findTableName("Users", self.tables):
            self.cur.execute("""
                CREATE TABLE Users (
                email VARCHAR(255) NOT NULL PRIMARY KEY,
                userId VARCHAR(255) NOT NULL
            )
            """)
            self.con.commit()
        if not findTableName("YouTubeKeys", self.tables):
            self.cur.execute("""
                CREATE TABLE YouTubeKeys (
                userId VARCHAR(255) NOT NULL PRIMARY KEY,
                youTubeKey VARCHAR(255) NOT NULL
            )
            """)
            self.con.commit()

        self.tables = self.cur.execute("SELECT name FROM sqlite_master").fetchall()
        print("tables: ", self.tables)

    def set_consumer(self, user_id: str, consumer_key: str, consumer_secret: str) -> None:
        consumerTuple = self.get_consumer(user_id)
        params = {"userId": user_id, "consumerKey": consumer_key, "consumerSecret": consumer_secret}
        if consumerTuple is None:
            self.cur.execute(
                f"""
                INSERT INTO Consumers (userId, consumerKey, consumerSecret) VALUES (:userId, :consumerKey, :consumerSecret)        
                """, params)
        else:
            self.cur.execute(
                f"""
            UPDATE Consumers 
            SET consumerKey = :consumerKey, consumerSecret = :consumerSecret
            WHERE userId = :userId
            """, params)
        self.con.commit()

    def get_consumer(self, user_id: str) -> list[str, str | None, str | None] | None:
        params = {"userId": user_id}
        return self.cur.execute(
            f"""
                SELECT userId, consumerKey, consumerSecret, requestKey, requestSecret, responseQueryString, accessKey, accessSecret, uploadIndex, uploadFinished
                FROM Consumers
                WHERE userId = :userId
            """, params).fetchone()

    def get_consumer_all(self, user_id: str) -> Consumer | None:
        result = self.get_consumer(user_id)
        print("result:", result)
        if result is not None:
            return Consumer(
                user_id=result[0],
                consumer_key=result[1],
                consumer_secret=result[2],
                request_key=result[3],
                request_secret=result[4],
                response_query_string=result[5],
                access_key=result[6],
                access_secret=result[7],
                upload_index=result[8],
                upload_status=result[9]
            )
        else:
            return None

    def set_requests_token(self, user_id: str, request_key: str, request_secret: str) -> None:
        params = {"userId": user_id, "requestKey": request_key, "requestSecret": request_secret}
        self.cur.execute(f"""
            UPDATE Consumers 
            SET requestKey = :requestKey, requestSecret = :requestSecret
            WHERE userId = :userId
            """, params)
        self.con.commit()

    def get_requests_token(self, user_id: str) -> tuple[str, str | None] | None:
        params = {"userId": user_id}
        return self.cur.execute(f"""
            SELECT userId, requestKey, requestSecret 
            FROM Users
            WHERE userId = :userId
        """, params).fetchone()

    def set_response_query_string(self, user_id: str, request_qs: str) -> None:
        params = {"userId": user_id, "responseQueryString": request_qs}
        self.cur.execute(f"""
                    UPDATE Consumers 
                    SET responseQueryString = :responseQueryString
                    WHERE userId = :userId
                    """, params)
        self.con.commit()

    def set_access_key_and_secret(self, user_id: str, access_key: str, access_secret: str) -> None:
        params = {"userId": user_id, "accessKey": access_key, "accessSecret": access_secret}
        self.cur.execute(f"""
                            UPDATE Consumers 
                            SET accessKey = :accessKey, accessSecret = :accessSecret
                            WHERE userId = :userId
                            """, params)
        self.con.commit()

    def set_upload_index(self, user_id: str, index: int) -> None:
        params = {"userId": user_id, "uploadIndex": index}
        self.cur.execute(f"""
                            UPDATE Consumers 
                            SET uploadIndex = :uploadIndex
                            WHERE userId = :userId
                            """, params)
        self.con.commit()

    def release_authentication(self, user_id: str) -> None:
        params = {
            "userId": user_id,
            "requestKey": None,
            "requestSecret": None,
            "responseQueryString": None,
            "accessKey": None,
            "accessSecret": None,
            "uploadIndex": None,
        }
        self.cur.execute(f"""
                                    UPDATE Consumers 
                                    SET requestKey = :requestKey, requestSecret = :requestSecret, responseQueryString = :responseQueryString, accessKey = :accessKey, accessSecret = :accessSecret, uploadIndex = :uploadIndex
                                    WHERE userId = :userId
                                    """, params)
        self.con.commit()

    def set_upload_finished(self, user_id: str, status: bool) -> None:
        params = {"userId": user_id, "status": status}
        self.cur.execute(f"""
                            UPDATE Consumers 
                            SET uploadFinished = :status
                            WHERE userId = :userId
                            """, params)
        self.con.commit()

    def add_user(self, email: str) -> tuple[str, str] | None:
        new_uuid = str(uuid.uuid4())
        params = {"email": email, "userId": new_uuid}
        try:
            self.cur.execute(
                f"""
                INSERT INTO Users VALUES (:email, :userId)        
                """, params)
            self.con.commit()
        except:
            return None
        return params["email"], params["userId"]

    def get_user(self, email: str) -> str | None:
        params = {"email": email}
        res = self.cur.execute(
            f"""
            SELECT userId
            FROM Users
            WHERE email = :email
            """, params).fetchone()
        print(res)
        if res is None:
            return None
        else:
            return res[0]

    def set_youtube_key(self, user_id: str, youtube_key: str) -> None:
        found_youtube_key = self.get_youtube_key(user_id)
        if found_youtube_key is None:
            params = {"userId": user_id, "youtubeKey": youtube_key}
            self.cur.execute(f"""
                        INSERT INTO YouTubeKeys VALUES (:userId, :youtubeKey)        
                        """, params)
            self.con.commit()
        else:
            params = {"userId": user_id, "youtubeKey": youtube_key}
            self.cur.execute(f"""
                                UPDATE YouTubeKeys 
                                SET youTubeKey = :youtubeKey
                                WHERE userId = :userId
                                """, params)
            self.con.commit()

    def get_youtube_key(self, user_id: str) -> tuple[str, str] | None:
        params = {"userId": user_id}
        res = self.cur.execute(
            f"""
                            SELECT userId, youTubeKey
                            FROM YouTubeKeys
                            WHERE userId = :userId
                            """, params).fetchone()
        print(res)
        return res

    def close(self):
        self.con.close()
