import asyncio
from datetime import datetime, timezone
from nanoid import generate as nanoid
from yarl import URL
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Annotated
from fastapi import Depends

from .objects import Activity, Object, CollectionPage, gather_ids
from .storage.elastic import ElasticStorage, Query, SearchResults

Node = dict | Object | str | URL

class Forbidden(Exception):
    pass

storage: ContextVar[ElasticStorage] = ContextVar("var", default=ElasticStorage())
stock: dict[str, Object] = {}

class Bus:
    identity: str

    def __init__(self, identity: Node | None):
        if identity is None:
            self.identity = None
        else:
          self.identity = get_id(identity).rstrip('/')

    async def send(self, activity: Activity):
        outbox = get_url(self.identity).joinpath('outbox')
        url = outbox.joinpath(nanoid())
        activity.attributed_to = [self.identity]
        activity.id = str(url)
        activity.published = datetime.now(tz=timezone.utc)
        activity.updated = datetime.now(tz=timezone.utc)
        activity.actor = self.identity
        await storage.get().add(str(outbox), activity, refresh=True)
    
    async def recieve(self, activity: Object):
        raise NotImplementedError()
    
    async def dereference(self, node: Node):
        # Todo: multi-layer caching
        url = get_url(node)

        if url.path in stock:
            obj = stock[url.path]
        elif str(url) in stock:
            obj = stock[str(url)]
        else:
            obj = await storage.get().load(url)
        
        if obj and not await self.can_read(obj):
            raise Forbidden()

        return obj
    
    async def load_collection_page(self, url: Node, size: int = 42, after: str = None):
        url = get_url(url)

        await self.dereference(url) # Ensure collection exists and we can read it

        query = Query(collection=str(url), size=size, after=after)
        results: SearchResults = await storage.get().search(query)
        
        page = CollectionPage(type="CollectionPage", part_of=str(url), total_items=results.total, items=results.hits)
        if results.total == 0:
            return page
        
        page.first = str(url.with_query({'after': ''}))
        page.next = str(url.with_query({'after': results.sort}))
        return page
    
    async def query(self, query: Query):
        return self.storage.get().search(query)

    async def can_read(self, object: Object):
        # TODO: Check for every group token is in

        if self.identity == 'sys':
            return True

        if is_public(object.audience):
            return True
        
        if self.identity:
          if self.identity in gather_ids(object.attributed_to):
              return True
          if self.identity in gather_ids(object.audience):
              return True

        url = URL(object.id)
        if (url.path == '/'):
            return False

        collection = await self.dereference(url.parent or '/')
        if collection is None:
            return False
        return await self.can_read(collection)

    async def can_write(self, node: Node):
        # TODO: Check for every group token is in 
        url = get_url(node)

        if not self.identity:
            return False

        if self.identity == 'sys':
            return True
        
        object = await self.dereference(url)
        
        if object and self.identity in gather_ids(object.attributed_to):
            return True
        
        if url.path == '/':
            return False
        
        return await self.can_write(url.parent)


def is_public(*values):
    ids = gather_ids(*values)
    keys = ['https://www.w3.org/ns/activitystreams#Public', 'Public', 'as:Public']
    for key in keys:
        if key in ids:
            return True
    return False


def get_url(node: Node):
    match node:
        case Object(id=id):
            url = URL(id)
        case {"id": id}:
            url = URL(id)
        case str():
            url = URL(node)
        case URL():
            url = node
        case _:
            raise ValueError(f"Node is {node!r}")
    if url.path == '/':
        return url
    if not url.host:
        return URL(url.path)
    return url.origin().with_path(url.path)

def get_id(node: Node):
    return str(get_url(node))
