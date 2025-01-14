from typing import Union, Annotated
from enum import Enum
import strawberry
from requests_oauthlib import OAuth1

from ImportHelper.ImportJob import run_import_job, WLPImportData, WLPVideo
from dbs.DBSIndri import DatabaseIndri, db_semaphore
from dbs.FileDB import FileDB
from AuthHelper import get_authentication_link


@strawberry.input
class UserConsumerInput:
    id: str
    key: str
    secret: str


@strawberry.input
class UserIdInput:
    id: strawberry.ID


@strawberry.input
class UserIdInput:
    id: strawberry.ID


@strawberry.input
class UserYouTubeInput:
    id: strawberry.ID
    youTubeKey: str


@strawberry.input
class WLPVideoInput:
    watchId: strawberry.ID
    categories: list[str]


@strawberry.input
class WLPImportInput:
    user_id: strawberry.ID
    wlpVideos: list[WLPVideoInput]


@strawberry.type
class User:
    id: strawberry.ID
    email: str


@strawberry.type
class UserConsumer:
    id: strawberry.ID
    key: str
    secret: str


@strawberry.type
class NoConsumerRegistered:
    id: strawberry.ID


@strawberry.type()
class UserYouTubeKey:
    id: strawberry.ID
    youTubeKey: str


@strawberry.type
class NoYouTubeKeyRegistered:
    id: strawberry.ID


@strawberry.type
class AuthenticationConsumerLink:
    id: strawberry.ID
    url: str


@strawberry.enum
class AuthenticationStatus(Enum):
    AUTHENTICATED = "authenticated"
    PENDING = "pending"
    UNAUTHENTICATED = "unauthenticated"


@strawberry.type
class AuthenticationAnswer:
    id: strawberry.ID
    status: AuthenticationStatus

@strawberry.type
class UploadAnswer:
    id: strawberry.ID
    message: str

@strawberry.type
class Mutation:

    @strawberry.mutation
    def create_or_update_consumer(self, consumer_input: UserConsumerInput) -> UserConsumer:
        dbIndri = DatabaseIndri()
        dbIndri.set_consumer(consumer_input.id, consumer_input.key, consumer_input.secret)
        dbIndri.close()
        return UserConsumer(id=strawberry.ID(consumer_input.id), key=consumer_input.key, secret=consumer_input.secret)

    @strawberry.mutation
    def create_user(self, email: str) -> User:
        dbIndri = DatabaseIndri()
        (_, user_id) = dbIndri.add_user(email)
        dbIndri.close()
        return User(id=strawberry.ID(user_id), email=email)

    @strawberry.mutation
    def create_or_update_youtube_key(self, key_input: UserYouTubeInput) -> UserYouTubeKey:
        dbIndri = DatabaseIndri()
        dbIndri.set_youtube_key(key_input.id, key_input.youTubeKey)
        dbIndri.close()
        return UserYouTubeKey(id=strawberry.ID(key_input.id), youTubeKey=key_input.youTubeKey)

    @strawberry.mutation
    def verify_upload_wlp_videos_to_wiki(self, wlp_import: WLPImportInput) -> AuthenticationConsumerLink:
        dbIndri = DatabaseIndri()
        consumer = dbIndri.get_consumer_all(wlp_import.user_id)
        print(consumer.consumer_key, consumer.consumer_secret)
        (redirect, req_key, req_sec) = get_authentication_link(consumer.consumer_key, consumer.consumer_secret)
        dbIndri.set_requests_token(wlp_import.user_id, req_key, req_sec)
        dbIndri.close()
        wlp_videos = list(map(lambda x: WLPVideo(x.watchId, x.categories), wlp_import.wlpVideos))
        wlp_import_data = WLPImportData(wlp_import.user_id, wlp_videos)
        file_db = FileDB(wlp_import.user_id)
        file_db.upload_pickle(wlp_import_data)
        return AuthenticationConsumerLink(id=wlp_import.user_id, url=redirect)

    @strawberry.mutation
    def start_wlp_videos_import(self, user_id: str) -> UploadAnswer:
        try:
            file_db = FileDB(user_id)
            wlp_import = file_db.read_pickle()
            db_semaphore.acquire()
            db_indri = DatabaseIndri()
            consumer = db_indri.get_consumer_all(user_id)
            (_, youtube_key) = db_indri.get_youtube_key(user_id)
            db_indri.set_upload_index(user_id, 0)
            db_indri.close()
            db_semaphore.release()
            auth1 = OAuth1(consumer.consumer_key,
                           client_secret=consumer.consumer_secret,
                           resource_owner_key=consumer.access_key,
                           resource_owner_secret=consumer.access_secret)
            run_import_job(
                o_auth=auth1,
                wlp_video_import=wlp_import,
                youtube_key=youtube_key
            )
            return UploadAnswer(id=wlp_import.user_id, message="Started") # make new id? like upload_id
        except:
            return UploadAnswer(id=strawberry.ID(user_id), message="Failed")


@strawberry.type
class Query:

    @strawberry.field
    def get_user(self, email: str) -> User:
        dbIndri = DatabaseIndri()
        user_id = dbIndri.get_user(email)
        dbIndri.close()
        return User(id=strawberry.ID(user_id), email=email)

    @strawberry.field
    def get_consumer_token(self, user_id: str) -> Annotated[
        Union[UserConsumer, NoConsumerRegistered], strawberry.union("HasConsumerAnswer")]:
        dbIndri = DatabaseIndri()
        res = dbIndri.get_consumer(user_id)
        dbIndri.close()
        if res is None:
            return NoConsumerRegistered(id=strawberry.ID(user_id))
        return UserConsumer(id=strawberry.ID(user_id), key=res[1], secret=res[2])

    @strawberry.field
    def get_youtube_key(self, user_id: str) -> Annotated[
        Union[UserYouTubeKey, NoYouTubeKeyRegistered], strawberry.union("HasYouTubeKeyAnswer")]:
        dbIndri = DatabaseIndri()
        res = dbIndri.get_youtube_key(user_id)
        dbIndri.close()
        if res is None:
            return NoYouTubeKeyRegistered(id=strawberry.ID(user_id))
        return UserYouTubeKey(id=strawberry.ID(user_id), youTubeKey=res[1])

    # deprecated!!
    @strawberry.field
    def get_authentication_link(self, user_id: strawberry.ID) -> AuthenticationConsumerLink:
        dbIndri = DatabaseIndri()
        (_, con_key, con_secret) = dbIndri.get_consumer(user_id)
        (redirect, request_key, request_secret) = get_authentication_link(con_key, con_secret)
        dbIndri.set_requests_token(user_id, request_key, request_secret)
        dbIndri.close()
        return AuthenticationConsumerLink(id=strawberry.ID(user_id), url=redirect)

    @strawberry.field
    def is_authenticated(self, user_id: str) -> AuthenticationAnswer:
        db_semaphore.acquire()
        dbIndri = DatabaseIndri()
        res = dbIndri.get_consumer_all(user_id)
        dbIndri.close()
        db_semaphore.release()
        print("acces_tokens:", res.access_secret, res.access_key, "request_key:", res.request_key)
        if (res.access_secret is not None) and (res.access_key is not None):
            return AuthenticationAnswer(id=strawberry.ID(user_id), status=AuthenticationStatus.AUTHENTICATED)
        elif res.request_key is not None and res.response_query_string is None:
            print("Pending")
            return AuthenticationAnswer(id=strawberry.ID(user_id), status=AuthenticationStatus.PENDING)
        else:
            return AuthenticationAnswer(id=strawberry.ID(user_id), status=AuthenticationStatus.UNAUTHENTICATED)

    @strawberry.field
    def get_upload_status(self, user_id: str) -> UploadAnswer:
        db_semaphore.acquire()
        dbIndri = DatabaseIndri()
        res = dbIndri.get_consumer_all(user_id)
        dbIndri.close()
        db_semaphore.release()
        if (res is not None) and res.upload_status:
            db_semaphore.acquire()
            dbIndri = DatabaseIndri()
            dbIndri.set_upload_finished(user_id, None)
            dbIndri.close()
            db_semaphore.release()
            return UploadAnswer(id=strawberry.ID(user_id), message="Upload Done")
        elif (res is not None) and (res.upload_index is not None):
            return UploadAnswer(id=strawberry.ID(user_id), message=str(res.upload_index))
        else:
            return UploadAnswer(id=strawberry.ID(user_id), message="No upload")


schema = strawberry.Schema(query=Query, mutation=Mutation)
