import sqlite3
import os


from dbs.dslContext.findTableHelper import find_table_name


class YouTubeData:
    def __init__(self, user_id: str, key: str | None):
        self.user_id = user_id
        self.key = key


class YouTubeKeysDSL:
    def __init__(self, con, cur):
        self.con = con
        self.cur = cur

    def create_youtube_key_table(self):
        tables = self.cur.execute("SELECT name FROM sqlite_master").fetchall()
        params = {"tableName": "YouTubeKeys"}
        if not find_table_name(params["tableName"], tables):
            self.cur.execute(f"""
                                CREATE TABLE {params["tableName"]} (
                                userId VARCHAR(255) NOT NULL PRIMARY KEY,
                                youTubeKey VARCHAR(255)
                            )
                            """)
            self.con.commit()

    def set_or_update_youtube_key(self, user_id: str, key: str) -> YouTubeData:
        params = {"userId": user_id, "key": key}
        youtube_data = self.get_youtube_key(user_id)
        if youtube_data is None:
            self.cur.execute(f"""
                INSERT INTO YouTubeKeys (userId, youTubeKey) VALUES (:userId, :key)
            """, params)
        else:
            self.cur.execute(
                f"""
                                UPDATE YouTubeKeys 
                                SET youTubeKey = :key
                                WHERE userId = :userId
                                """, params)
        self.con.commit()
        return self.get_youtube_key(user_id)

    def get_youtube_key(self, user_id: str) -> YouTubeData | None:
        params = {"userId": user_id}
        result = self.cur.execute(f"""
            SELECT userId, youTubeKey FROM YouTubeKeys WHERE userId = :userId
        """, params).fetchone()
        if result is not None:
            return YouTubeData(result[0], result[1])
        else:
            return None
