import sqlite3
import uuid
import os

from dbs.DBSIndri import find_table_name


class ImportJobData:
    def __init__(self, upload_id: str, user_id: str, file_path: str, upload_index: int, upload_size: int,
                 upload_status: str):
        self.upload_id = upload_id
        self.user_id = user_id
        self.file_path = file_path
        self.upload_index = upload_index
        self.upload_size = upload_size
        self.upload_status = upload_status


class ImportJobsDSL:
    def __init__(self, con, cur):
        self.con = con
        self.cur = cur


    def create_import_jobs_table(self):
        tables = self.cur.execute("SELECT name FROM sqlite_master").fetchall()
        params = {"tableName": "ImportJobs"}
        if not find_table_name(params["tableName"], tables):
            self.cur.execute("""
                                CREATE TABLE :tableName (
                                uploadId VARCHAR(255) NOT NULL PRIMARY KEY,
                                userId VARCHAR(255) NOT NULL,
                                filePath VARCHAR(1023),
                                uploadIndex INTEGER,
                                uploadSize INTEGER,
                                uploadStatus VARCHAR(255),
                                startTimestamp TIMESTAMP,
                                endTimestamp TIMESTAMP
                                )
                                """, params)
            self.con.commit()

    def create_import_job(self, user_id: str, upload_size: int, file_path: str) -> ImportJobData:
        params = {"uploadId":  str(uuid.uuid4()), "userId": user_id, "uploadSize": upload_size, "filePath": file_path, "uploadIndex": 0, "uploadStatus": "OnGoing" }
        self.cur.execute(
            f"""
                INSERT INTO ImportJobs (uploadId, userId, filePath, uploadIndex, uploadSize, uploadStatus, startTimestamp) VALUES (:uploadId, :userId, :filePath, :uploadIndex, :uploadSize, :uploadStatus, {datetime.now()})        
                """, params)
        self.con.commit()
        return self.get_import_job(params["uploadId"])

    def get_import_job(self, upload_id) -> ImportJobData | None:
        params = {"uploadId": upload_id}
        t = self.cur.execute(
            f"""
                                SELECT uploadId, userId, filePath, uploadIndex, uploadSize, uploadStatus
                                FROM ImportJobs
                                WHERE uploadId = :uploadId
                            """, params).fetchone()
        if t is not None:
            return ImportJobData(t[0], t[1], t[2], t[3], t[4], t[5])
        else:
            return None

    def get_import_jobs(self, user_id: str) -> list[ImportJobData]:
        params = {"userId": user_id}
        results = self.cur.execute(
            f"""
                        SELECT uploadId, userId, filePath, uploadIndex, uploadSize, uploadStatus
                        FROM ImportJobs
                        WHERE userId = :userId
                    """, params).fetchall()
        return list(map(lambda t: ImportJobData(t[0], t[1], t[2], t[3], t[4], t[5]), results))

    def update_import_job_index(self, upload_id: str, upload_index: int) -> ImportJobData | None:
        params = {"uploadId": upload_id, "uploadIndex": upload_index}
        self.cur.execute(
            f"""
                   UPDATE ImportJobs 
                   SET uploadIndex = :uploadIndex
                   WHERE uploadId = :uploadId
                   """, params)
        self.con.commit()
        return self.get_import_job(upload_id)

    def update_import_job_status(self, upload_id: str, status: str) -> ImportJobData | None:
        params = {"uploadId": upload_id, "uploadStatus": upload_id}
        self.cur.execute(
            f"""
                           UPDATE ImportJobs 
                           SET uploadStatus = :uploadStatus
                           WHERE uploadId = :uploadId
                           """, params)
        self.con.commit()
        return self.get_import_job(upload_id)