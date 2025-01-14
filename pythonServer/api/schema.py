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
        db = DatabaseIndri()
        db.set_or_update_consumer(
            db.wikibase,
            userId=consumer_input.id,
            consumerKey=consumer_input.key,
            consumerSecret=consumer_input.secret
        )
        db.close()
        return UserConsumer(id=strawberry.ID(consumer_input.id), key=consumer_input.key, secret=consumer_input.secret)

    @strawberry.mutation
    def create_user(self, email: str) -> User:
        db = DatabaseIndri()
        (_, user_id) = db.add_user(email)
        db.close()
        return User(id=strawberry.ID(user_id), email=email)

    @strawberry.mutation
    def create_or_update_youtube_key(self, key_input: UserYouTubeInput) -> UserYouTubeKey:
        db = DatabaseIndri()
        db.set_or_update_youtube_key(key_input.id, key_input.youTubeKey)
        db.close()
        return UserYouTubeKey(id=strawberry.ID(key_input.id), youTubeKey=key_input.youTubeKey)

    @strawberry.mutation
    def verify_upload_wlp_videos_to_wiki(self, wlp_import: WLPImportInput) -> AuthenticationConsumerLink:
        db = DatabaseIndri()
        consumer = db.get_consumer(db.wikibase, wlp_import.user_id)
        print(consumer.consumer_key, consumer.consumer_secret)

        (redirect, req_key, req_sec) = get_authentication_link(consumer.consumer_key, consumer.consumer_secret)

        db.set_request_tokens(db.wikibase, wlp_import.user_id, req_key, req_sec)
        db.close()

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
            db = DatabaseIndri()
            consumer = db.get_consumer(db.wikibase, user_id)
            youtube_data = db.get_youtube_key(user_id)
            job_data = db.create_import_job(user_id, len(wlp_import.wlpVideos), file_db.path_pkl)
            db.close()
            db_semaphore.release()
            auth1 = OAuth1(client_key=consumer.consumer_key,
                           client_secret=consumer.consumer_secret,
                           resource_owner_key=consumer.access_key,
                           resource_owner_secret=consumer.access_secret)
            run_import_job(
                o_auth=auth1,
                wlp_video_import=wlp_import,
                youtube_key=youtube_data.key,
                job_data=job_data
            )
            return UploadAnswer(id=wlp_import.user_id, message=f"{job_data.upload_id}") # make new id? like upload_id
        except:
            return UploadAnswer(id=strawberry.ID(user_id), message="Failed")


@strawberry.type
class Query:

    @strawberry.field
    def get_user(self, email: str) -> User:
        db = DatabaseIndri()
        userData = db.get_user(email)
        db.close()
        return User(id=strawberry.ID(userData.user_id), email=email)

    @strawberry.field
    def get_consumer_token(self, user_id: str) -> Annotated[
        Union[UserConsumer, NoConsumerRegistered], strawberry.union("HasConsumerAnswer")]:
        db = DatabaseIndri()
        res = db.get_consumer(db.wikibase, user_id)
        db.close()
        if res is None:
            return NoConsumerRegistered(id=strawberry.ID(user_id))
        return UserConsumer(id=strawberry.ID(user_id), key=res.consumer_key, secret=res.consumer_secret)

    # deprecated!!
    @strawberry.field
    def get_authentication_link(self, user_id: strawberry.ID) -> AuthenticationConsumerLink:
        db = DatabaseIndri()
        consumer = db.get_consumer(db.wikibase, user_id)
        (redirect, request_key, request_secret) = get_authentication_link(consumer.consumer_key, consumer.access_secret)
        db.set_request_tokens(db.wikibase, user_id, request_key, request_secret)
        db.close()
        return AuthenticationConsumerLink(id=strawberry.ID(user_id), url=redirect)

    @strawberry.field
    def is_authenticated(self, user_id: str) -> AuthenticationAnswer:
        db_semaphore.acquire()
        db = DatabaseIndri()
        consumer = db.get_consumer(db.wikibase, user_id)
        db.close()
        db_semaphore.release()
        if (consumer.access_secret is not None) and (consumer.access_key is not None):
            return AuthenticationAnswer(id=strawberry.ID(user_id), status=AuthenticationStatus.AUTHENTICATED)
        elif (consumer.request_key is not None) and (consumer.response_query_string is None):
            return AuthenticationAnswer(id=strawberry.ID(user_id), status=AuthenticationStatus.PENDING)
        else:
            return AuthenticationAnswer(id=strawberry.ID(user_id), status=AuthenticationStatus.UNAUTHENTICATED)

    @strawberry.field
    def get_upload_status(self, upload_id: str) -> UploadAnswer:
        db_semaphore.acquire()
        db = DatabaseIndri()
        job_data = db.get_import_job(upload_id)
        db.close()
        db_semaphore.release()
        if job_data is not None:
            return UploadAnswer(id=strawberry.ID(upload_id), message=job_data.upload_status)
        else:
            return UploadAnswer(id=strawberry.ID(upload_id), message="unknown upload id - No upload found")


schema = strawberry.Schema(query=Query, mutation=Mutation)
