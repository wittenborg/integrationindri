import json
import threading
import time

from isodate import parse_duration

from AuthHelper import get_csrf_token
from ImportHelper.RequestHelper import video_exists, get_youtube_video_data, category_exists, channel_exists, create_new_item
from dbs.DBSIndri import DatabaseIndri, db_semaphore
from dbs.FileDB import FileDB

from requests_oauthlib import OAuth1
import datetime

from dbs.dslContext.ImportJobsClassDSL import ImportJobData


def base_entity():
    return {
        "labels": {},
        "description": {},
        "claims": {}
    }


def get_literal(prop: str, value: str | dict, _type: str, data_type: str):
    return {
        "mainsnak": {
            "snaktype": "value",
            "property": prop,
            "datavalue": {
                "value": value,
                "type": _type
            },
            "datatype": data_type
        },
        "type": "statement",
        "rank": "normal"
    }


def get_entity_number(entity: str):
    return int(entity.split("/").pop()[1:])


def get_entity(prop: str, entity_id: int):
    return {
        "mainsnak": {
            "snaktype": "value",
            "property": prop,
            "datavalue": {
                "value": {
                    "entity-type": "item",
                    "id": f"Q{entity_id}",
                    "numeric-id": entity_id
                },
                "type": "wikibase-entityid"
            },
            "datatype": "wikibase-item"
        },
        "type": "statement",
        "rank": "normal"
    }


def get_qualifier_literal(prop: str, value: str | dict, _type: str, data_type: str):
    qual = get_literal(prop, value, _type, data_type)["mainsnak"]
    qual.pop('type', None)
    qual.pop('rank', None)
    return qual


def get_qualifier_entity(prop: str, entity_id: int):
    qual = get_entity(prop, entity_id)["mainsnak"]
    qual.pop('type', None)
    qual.pop('rank', None)
    return qual


def get_duration(d: str):
    return {"P26": [get_literal("P26", d, "string", "string")]}


def get_subtitle_languages(strs: list[str]):
    return {"P25": list(map(lambda s: get_literal("P25", s, "string", "string"), strs))}


def get_categories(categories_entities: list[str]):
    return {"P4": list(map(lambda ce: get_entity("P4", get_entity_number(ce)), categories_entities))}


def get_reference(url: str, retrieved: str, hosted_by_entity: str, published_in_entity: str):
    return {"P10": [{
        **get_literal("P10", url, "string", "url"),
        "qualifiers": {
            "P11": [get_qualifier_literal("P11", {
                "time": f"+{retrieved}",
                "timezone": 0,
                "before": 0,
                "after": 0,
                "precision": 11,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
            }, "time", "time")],
            "P14": [get_qualifier_entity("P14", get_entity_number(hosted_by_entity))],
            "P28": [get_qualifier_entity("P28", get_entity_number(published_in_entity))]
        }}]}


def get_thumbnail(url: str):
    return {"P7": [get_literal("P7", url, "string", "url")]}


def get_in_languages(langs: list[str]):
    return {"P8": list(map(lambda l: get_literal("P8", l, "string", "string"), langs))}


def get_publication_date(date: str):
    return {"P6": [get_literal("P6", {
        "time": f"+{date}",
        "timezone": 0,
        "before": 0,
        "after": 0,
        "precision": 11,
        "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
    }, "time", "time")]}


def get_video_instance():
    return {"P1": [get_entity("P1", get_entity_number("https://bnwiki.wikibase.cloud/entity/Q4"))]}


def get_category_instance():
    return {"P1": [get_entity("P1", get_entity_number("https://bnwiki.wikibase.cloud/entity/Q10"))]}


def get_channel_instance():
    return {"P1": [get_entity("P1", get_entity_number("https://bnwiki.wikibase.cloud/entity/Q3"))]}


def get_label(label: str):
    return {
        "labels": {
            "en": {
                "language": "en",
                "value": label
            },
        }
    }


def try_get(key, data):
    try:
        return data[key]
    except KeyError:
        return None


class WikibaseVideo:
    title: str
    publication_date: str | None
    in_languages: list[str] | None
    thumbnails: str | None
    url: str
    published_by: str | None
    hosted_by: str | None
    categories: list[str] | None
    subtitles_languages: list[str] | None
    duration: str | None


def create_wiki_base_video(data: WikibaseVideo):
    base = {
        "labels": {},
        "description": {},
        "claims": {**get_video_instance()}
    }

    title = data.title
    if title is not None:
        base["labels"] = get_label(title)["labels"]

    publication_date = data.publication_date
    if publication_date is not None:
        base["claims"] = {**base["claims"], **get_publication_date(publication_date)}

    language = data.in_languages
    if language is not None:
        base["claims"] = {**base["claims"], **get_in_languages(language)}

    thumbnail_url = data.thumbnails
    if thumbnail_url is not None:
        base["claims"] = {**base["claims"], **get_thumbnail(thumbnail_url)}

    url = data.url
    published_by = data.published_by
    hosted_by = data.hosted_by
    if url is not None and published_by is not None and hosted_by is not None:
        now = datetime.date.today().isoformat()
        base["claims"] = {**base["claims"], **get_reference(url, f"{now}T00:00:00Z", hosted_by, published_by)}

    categories = data.categories
    if categories is not None:
        base["claims"] = {**base["claims"], **get_categories(categories)}

    subtitle_languages = data.subtitles_languages
    if subtitle_languages is not None:
        base["claims"] = {**base["claims"], **get_subtitle_languages(subtitle_languages)}

    duration = data.duration
    if duration is not None:
        base["claims"] = {**base["claims"], **get_duration(duration)}

    return base


def create_category_wikibase(category_name: str) -> dict:
    return {
        **get_label(category_name),
        "description": {},
        "claims": {**get_category_instance()}
    }


def create_channel_wikibase(channel_name: str, channel_id: str) -> dict:
    return {
        **get_label(channel_name),
        "description": {},
        "claims": {**get_channel_instance(), "P30": [get_literal("P30", channel_id, "string", "string")]}
    }


def split_array(batch_size: int, array: list) -> list[list]:
    l = []
    for i in range(0, len(array), batch_size):
        l.append(array[i:i + batch_size])
    return l


class WLPVideo:
     def __init__(self, watch_id: str, categories: list[str]):
         self.watch_id = watch_id
         self.categories = categories

     def __str__(self):
         return f"{self.watch_id} {self.categories}"

     def __repr__(self):
         return f"{self.watch_id} {self.categories}"

class WLPImportData:

    def __init__(self, user_id: str, data: list[WLPVideo]):
        self.user_id = user_id
        self.wlp_videos = data

class ImportJob:

    def __init__(self,
                 o_auth: OAuth1,
                 youtube_key: str,
                 wlp_video_import: WLPImportData,
                 job_data: ImportJobData
                 ):
        self.o_auth = o_auth
        self.youtube_key = youtube_key
        self.job_data = job_data

        self.user_id = wlp_video_import.user_id
        self.batch_size = 50
        self.wlp_videos_batches = split_array(self.batch_size, wlp_video_import.wlp_videos)

        self.category_cache = {}
        self.channel_cache = {}
        self.batch_index = 0
        self.video_in_batch_index = 0

    def aggregate_categories(self, wlp_videos, csrf_token):

        # flatten all categories list over all wlp_videos
        category_set = set()
        for wlp_video in wlp_videos:
            category_set.update(wlp_video.categories)

        # remove categories from set that are already in cache
        category_tmp = set()
        for category in category_set:
            found_category_in_cache = try_get(category, self.category_cache)
            if found_category_in_cache is not None:
                category_tmp.add(category)

        category_set = category_set.difference(category_tmp)

        # find the missing ones in wikibase
        found_category_in_wikibase = category_exists(list(category_set))

        for found_category in found_category_in_wikibase:
            if found_category_in_wikibase[found_category] is None:
                entity = create_new_item(create_category_wikibase(found_category), self.o_auth, csrf_token)
                # print("new category:", entity)
                self.category_cache[found_category] = "https://bnwiki.wikibase.cloud/entity/" + entity["entity"]["id"]
            else:
                self.category_cache[found_category] = found_category_in_wikibase[found_category]

    # - assumes cache is always valid
    def aggregate_channels(self, channels: dict, csrf_token):

        # filter out channels that already exists in cache
        channels_tmp = []
        for channel_id in channels:
            found_id_in_cache = try_get(channel_id, self.channel_cache)
            if found_id_in_cache is not None:
                channels_tmp.append(channel_id)

        for c_tmp in channels_tmp:
            channels.pop(c_tmp)

        # check if some missing channels already exists in wikibase
        found_channels_in_wikibase = channel_exists(list(channels.keys()))

        # create channel, if it is missing in wikibase, else add it to cache
        for found_channel in found_channels_in_wikibase:
            if found_channels_in_wikibase[found_channel] is None:
                entity = create_new_item(
                    create_channel_wikibase(channels[found_channel]["channel_name"], found_channel),
                    self.o_auth,
                    csrf_token)
                # print("new channel:", entity)
                self.channel_cache[found_channel] = "https://bnwiki.wikibase.cloud/entity/" + entity["entity"]["id"]
            else:
                self.channel_cache[found_channel] = found_channels_in_wikibase[found_channel]

    def update_caches(self, youtube_videos, wlp_videos, csrf_token):
        self.aggregate_categories(wlp_videos, csrf_token)

        channels_by_id = {}
        for video in youtube_videos:
            channel_id = try_get("channelId", video["snippet"])
            channel_name = try_get("channelTitle", video["snippet"])
            channels_by_id[channel_id] = {"channel_name": channel_name}

        self.aggregate_channels(channels_by_id, csrf_token)


    def remove_existing_videos(self, wlp_videos: list[WLPVideo]) -> list[WLPVideo]:
        wlp_videos_set = set(list(map(lambda v: f"https://www.youtube.com/watch?v={v.watch_id}", wlp_videos)))
        found_vidoes_in_wikibase = video_exists(
            list(map(lambda v: f"https://www.youtube.com/watch?v={v.watch_id}", wlp_videos)))
        found_videos_set = set(list(filter(lambda found_id: found_vidoes_in_wikibase[found_id] is not None, found_vidoes_in_wikibase.keys())))
        diff_videos_set = wlp_videos_set.difference(found_videos_set)
        return list(filter(lambda wlp_video: f"https://www.youtube.com/watch?v={wlp_video.watch_id}" in diff_videos_set, wlp_videos))


    def create_video_by_watch_id(self, video, wlp_videos, csrf_token):
        snippet = video["snippet"]
        content_details = video["contentDetails"]

        watch_id = try_get("id", video)
        published_at = try_get("publishedAt", snippet)
        if published_at is not None:
            published_at = f"{published_at[0: 10]}T00:00:00Z"
        title = try_get("title", snippet)
        channel_id = try_get("channelId", snippet)
        thumbnail_url = try_get("url", snippet["thumbnails"]["medium"])
        in_language = try_get("defaultAudioLanguage", snippet)
        duration = try_get("duration", content_details)
        if duration is not None:
            duration = str(int(parse_duration(duration).total_seconds()))

        categories_list = []
        for wlp_video in wlp_videos:
            if wlp_video.watch_id == watch_id:
                categories_list = wlp_video.categories

        categories_wikibase = []
        for category in categories_list:
            categories_wikibase.append(self.category_cache[category])

        channel_wikibase = self.channel_cache[channel_id]

        wikibase_video = WikibaseVideo()
        wikibase_video.title = title
        wikibase_video.publication_date = published_at
        if in_language is not None:
            wikibase_video.in_languages = [in_language]
        else:
            wikibase_video.in_languages = None
        wikibase_video.thumbnails = thumbnail_url
        wikibase_video.url = "https://www.youtube.com/watch?v=" + watch_id
        wikibase_video.published_by = channel_wikibase
        wikibase_video.hosted_by = "https://bnwiki.wikibase.cloud/entity/Q8"
        wikibase_video.categories = categories_wikibase
        wikibase_video.duration = duration
        wikibase_video.subtitles_languages = None

        wikibase_video_dict = create_wiki_base_video(wikibase_video)
        return create_new_item(wikibase_video_dict, self.o_auth, csrf_token), wikibase_video_dict

    # would be faster to map wlp_videos to a dict based on watch_id -> would filter dups
    def process_batch(self, wlp_videos: list[WLPVideo], batch_index):
        copy_wlp_videos = wlp_videos.copy()
        # if we don't do this we create duplicates! overwriting is a use case for later
        wlp_videos = self.remove_existing_videos(wlp_videos)
        print("wlp_videos:", wlp_videos)

        time.sleep(2)

        if len(wlp_videos) == 0:
            db_semaphore.acquire()
            db = DatabaseIndri()
            db.update_import_job(
                self.job_data.upload_id,
                uploadIndex=self.batch_size * (batch_index + 1),
            )
            db.close()
            db_semaphore.release()
            return

        # wlp_videos != youtube_videos, because some videos may not exists anymore
        youtube_videos = get_youtube_video_data(self.youtube_key, list(map(lambda v: v.watch_id, wlp_videos)))["items"]
        # print("youtube_videos_count:", len(youtube_videos))
        # print("youtube_videos:", list(map(lambda x: x["id"], youtube_videos)))

        csrf_token = get_csrf_token(self.o_auth)
        self.update_caches(youtube_videos, wlp_videos, csrf_token)
        # print("category_cache:", self.category_cache)
        # print("channel_cache:", self.channel_cache)

        failed_entities = {}
        successful_entities = {}
        failed_at_wikibase_dict_creation = []

        for video in youtube_videos:
            try:
                (entity, wikibase_dict) = self.create_video_by_watch_id(video, wlp_videos, csrf_token)
                if entity["success"] != 1:
                    failed_entities[video["id"]] = { "response": entity, "send_data": wikibase_dict }
                else:
                    successful_entities[video["id"]] = {"response": entity, "send_data": wikibase_dict }
            except:
                failed_at_wikibase_dict_creation.append(video["id"])

            # update db latest imported video index
            for wlp_video_index in range(0, len(copy_wlp_videos)):
                if copy_wlp_videos[wlp_video_index].watch_id == video["id"]:
                    db_semaphore.acquire()
                    db = DatabaseIndri()
                    db.update_import_job(
                        self.job_data.upload_id,
                        uploadIndex=self.batch_size * batch_index + wlp_video_index,
                    )
                    db.close()
                    db_semaphore.release()

        # logging
        file_db = FileDB("logs", f"log_import_wlp_videos_{batch_index}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
        file_db.upload({
            "failed_entities": failed_entities,
            "successful_entities": successful_entities,
            "failed_at_wikibase_dict_creation": failed_at_wikibase_dict_creation
        })

    def process(self):
        for batchIndex in range(0, len(self.wlp_videos_batches)):
            self.process_batch(self.wlp_videos_batches[batchIndex], batchIndex)

        file_db = FileDB(self.user_id)
        file_db.delete_pickle()
        db_semaphore.acquire()
        db = DatabaseIndri()
        db.release_authentication(db.wikibase, self.user_id)
        db.update_import_job(
            self.job_data.upload_id,
            uploadStatus="Done",
            uploadIndex=self.job_data.upload_size,
            endTimestamp=datetime.datetime.now()
        )
        db.close()
        db_semaphore.release()
        print("DONE")
        return None

def run_import_job(
                 o_auth: OAuth1,
                 youtube_key: str,
                 wlp_video_import: WLPImportData,
                 job_data: ImportJobData
):
    import_job = ImportJob(o_auth, youtube_key, wlp_video_import, job_data)
    print("!IMPORT THREAD STARTED!")
    threading.Thread(target=import_job.process, daemon=True).start()


if __name__ == "__main__":
    """
    import_job = ImportJob(
        o_auth=None,
        csrf_token=None,
        youtube_key="AIzaSyBDb9q9lMnzeIbNauMLhCN2Gn1HHITRxo4",
        wlp_video_import=WLPImportInput(wlpVideos=[WLPVideo(watchId="fhbShczKosk",
                                                            categories=['Economics', 'Philosophy', 'Political Science',
                                                                        'Social Science', 'Humanities'])],
                                        user_id="asd")
    )

    import_job.process_batch([WLPVideo(watchId="fhbShczKosk",
                                       categories=['Economics', 'Philosophy', 'Political Science', 'Social Science',
                                                   'Humanities'])])
    """
