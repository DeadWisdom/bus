import asyncio, weakref
from yarl import URL
from typing import Any, Iterator
from enum import Enum
from pydantic import BaseModel
from elasticsearch import AsyncElasticsearch, Elasticsearch, NotFoundError
from valet.bus import Object
from valet.settings import Settings

settings = Settings()


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class Query(BaseModel):
    text: str | dict[str, str] | None = None
    keywords: dict[str, str] | None = None
    sort: dict[str, SortOrder] | list[dict[str, SortOrder]] | None = [{"updated": SortOrder.desc}, {"id": SortOrder.asc}]
    size: int = 42
    after: Any = None
    collection: str | None = None
    type: str | None = None

    def gather_keywords(self):
        keywords = dict(self.keywords or {})
        if self.collection:
            keywords["_collection"] = self.collection
        if self.type:
            keywords["type"] = self.type
        return keywords

    def build(self):
        query = {}
        must = []
        keywords = self.gather_keywords()

        body = {"query": query, "size": self.size}

        match self.text:
            case str():
                query["query_string"] = self.text
            case dict():
                must.append({"match": self.text})

        if keywords:
            for key, value in keywords.items():
                must.append({"term": {key: value}})

        if must:
            query["bool"] = {"must": must}

        if not query:
            query["match_all"] = {}

        if self.after:
            body["search_after"] = self.after

        match self.sort:
            case dict():
                body["sort"] = [self.sort]
            case list():
                body["sort"] = self.sort

        return body
    

class SearchResults(BaseModel):
    query: Query
    hits: list[Object]
    sort: Any = None
    elapsed: float
    total: int

    def __iter__(self) -> Iterator[Object]:
        return iter(self.hits)
    
    def more(self, sort=None, **kwargs):
        kwargs.setdefault("after", self.sort)
        return self.query.model_copy(update=kwargs)
    
    def __bool__(self):
        return self.total > 0
    
    def __getitem__(self, index):
        return self.hits[index]
    
    def first(self):
        return self.hits[0] if self.hits else None


class ElasticStorage:
    prefix: str = ""

    def __init__(self, client=None, prefix=""):
        self.prefix = prefix
        self.client = client or AsyncElasticsearch(
            cloud_id=settings.elastic_cloud_id,
            api_key=settings.elastic_key,
        )
        weakref.finalize(self, self.close)

    def close(self):
        asyncio.run(self.aclose())

    async def aclose(self):
        await self.client.close()

    async def refresh(self):
        for index in INDEXES:
            await self.client.indices.refresh(index=self.prefix + index)

    async def store(self, object: Object, index="objects", refresh=False):
        index = self.prefix + index
        if not object.id:
            raise ValueError("Object must have an ID to be stored.")
        data = object.model_dump(by_alias=True)
        await self.client.index(index=index, id=object.id, body=data, refresh=refresh)
        return object

    async def load(self, id: str, index="objects", model_type=Object, refresh=False):
        id = str(id)
        index = self.prefix + index
        try:
            response = await self.client.get(index=index, id=id, refresh=refresh)
        except NotFoundError:
            return None
        return model_type.model_validate(response["_source"])
    
    async def delete(self, id: str, index="objects", refresh=False):
        id = str(id)
        index = self.prefix + index
        await self.client.delete(index=index, id=id, refresh=refresh)

    async def add(self, collection: str, object: Object, index="collections", refresh=False):
        collection = str(collection)
        index = self.prefix + index
        data = object.model_dump(by_alias=True)
        data["_collection"] = collection
        result = await self.client.index(index=index, body=data, refresh=refresh)
        return result["_id"]

    async def remove(self, collection: str, id: str, index="collections", refresh=False):
        collection = str(collection)
        id = str(id)
        index = self.prefix + index
        query = {"bool": {"must": [{"term": {"id": id}}, {"term": {"_collection": collection}}]}}
        await self.client.delete_by_query(index=index, query=query, refresh=refresh)

    async def search(self, query: Query, index="collections", refresh=False, model_type=Object):
        index = self.prefix + index
        if refresh:
            await self.client.indices.refresh(index=index)
        body = query.build()
        response = await self.client.search(index=index, body=body)
        objects = [model_type.model_validate(hit["_source"]) for hit in response["hits"]["hits"]]
        if response["hits"]["hits"]:
            sort = response["hits"]["hits"][-1].get('sort', None)
        else:
            sort = None
        return SearchResults(
            query=query,
            hits=objects,
            sort = sort,
            elapsed = response["took"] / 1000,
            total = response["hits"]["total"]["value"],
        )

    async def setup(self):
        for name, mappings in INDEXES.items():
            print(f"  {self.prefix + name:<30}... ", end="")
            await self.client.indices.create(index=self.prefix + name, mappings=mappings)
            print("✅")

    async def clear_if_testing(self):
        assert self.prefix == 'testing-', "Can only clear testing indexes."
        for name in INDEXES:
            await self.client.delete_by_query(index=self.prefix + name, query={"match_all": {}})

    @classmethod
    def reset_testing(cls):
        with Elasticsearch(cloud_id=settings.elastic_cloud_id, api_key=settings.elastic_key) as client:
            for name in INDEXES:
                client.indices.refresh(index='testing-' + name)
                client.delete_by_query(index='testing-' + name, query={"match_all": {}}, refresh=True)


### Mapping ###
NODE = {"type": "object", "properties": {"id": {"type": "keyword"}, "type": {"type": "keyword"}}}
KEYWORD = {"type": "keyword"}
TEXT = {"type": "text"}
DATE = {"type": "date"}
COMMON = {
    "id": KEYWORD,
    "type": KEYWORD,
    "name": TEXT,
    "summary": TEXT,
    "content": TEXT,
    "audience": NODE,
    "attributed_to": NODE,
    "context": NODE,
    "generator": NODE,
    "published": DATE,
    "updated": DATE,
    "start_time": DATE,
    "end_time": DATE,
    "tag": NODE,
    "to": NODE,
    "bto": NODE,
    "cc": NODE,
    "bcc": NODE,
    "media_type": KEYWORD,
    "in_reply_to": NODE,
}
ACCOUNTS = {
    "id": KEYWORD,
    "type": KEYWORD,
    "name": TEXT,
    "oauth": KEYWORD,
    "published": DATE,
    "updated": DATE
}

INDEXES = {
    "collections": {"dynamic": False, "properties": dict(COMMON, _collection=KEYWORD)},
    "objects": {"dynamic": False, "properties": COMMON},
    "accounts": {"dynamic": False, "properties": ACCOUNTS},
}
