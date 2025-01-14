from uuid import uuid4

from dbs.DBSIndri import find_table_name


class UserData:
    def __init__(self, email: str, user_id: str | None):
        self.email = email
        self.user_id = user_id

class UserDSL:
    def __init__(self, con, cur):
        self.con = con
        self.cur = cur

    def create_user_table(self):
        tables = self.cur.execute("SELECT name FROM sqlite_master").fetchall()
        params = {"tableName": "Users"}
        if not find_table_name(params["tableName"], tables):
            self.cur.execute("""
                            CREATE TABLE :tableName (
                            email VARCHAR(255) NOT NULL PRIMARY KEY,
                            userId VARCHAR(255) NOT NULL
                        )
                        """, params)
            self.con.commit()

    def add_user(self, email: str) -> UserData | None:
        new_uuid = str(uuid4())
        params = {"email": email, "userId": new_uuid}
        try:
            self.cur.execute(
                """
                INSERT INTO Users VALUES (:email, :userId)        
                """, params)
            self.con.commit()
        except:
            return None
        return UserData(params["email"], params["userId"])

    def get_user(self, email: str) -> UserData | None:
        params = {"email": email}
        res = self.cur.execute(
            """
            SELECT userId
            FROM Users
            WHERE email = :email
            """, params).fetchone()
        if res is None:
            return None
        else:
            return UserData(email, res[0])