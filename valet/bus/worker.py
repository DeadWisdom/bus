import traceback, orjson
from collections import defaultdict
from datetime import datetime, timezone
from .objects import Activity, Object, gather
from nanoid import generate as nanoid

from .base import storage, Bus, get_url

def get_traceback_error_object(e: Exception):
    stack = traceback.format_list(traceback.extract_stack())
    return Object(type="Error", name=e.__class__.__name__, summary=str(e), content=orjson.dumps(stack).decode(), published=datetime.now(tz=timezone.utc), mimetype="application/json")

class Worker:
    raise_errors: bool = False

    def __init__(self, raise_errors=False):
        self.raise_errors = raise_errors
    
    async def __call__(self, act: Activity):
        act.start_time = datetime.now(tz=timezone.utc)
        try:
          await self.audit(act)
          await self.process(act)
          await self.deliver(act)
        except Exception as e:
          if self.raise_errors:
              raise
          act.result = gather(act.result, get_traceback_error_object(e))
        act.end_time = datetime.now(tz=timezone.utc)
        act.duration = (act.end_time - act.start_time).total_seconds()
        await storage.get().store(act)
        return act

    async def audit(self, act: Activity):
        pass
    
    async def process(self, act: Activity):
        rules = get_ruless(gather(act.type))
        for fn in rules:
            result = await fn(act)
            if result:
                act.result = gather(act.result, result)
    
    async def deliver(self, act: Activity):
        pass
    
    async def fail(self, act: Activity, result=None):
        act.former_type = act.type
        act.type = ["Tombstone"]
        if result:
            act.result = result
        await storage.get().store(act)


__rules = defaultdict(list)

def rule(name: str):
    def wrapper(func):
        __rules[name].append(func)
        return func
    return wrapper

def get_ruless(names: list[str]):
    rules = []
    for name in names:
        rules.extend(__rules.get(name, ()))
    return rules


@rule("Create")
async def create(act: Activity):
    bus = Bus(act.actor)
    objects = []
    obj: Object
    for obj in act.object:
      assert obj and obj.id, f"Object has no id: {obj!r}"
      url = get_url(obj)
      assert await bus.can_write(url), "Forbidden"
      if not obj.attributed_to:
          obj.attributed_to = act.actor
      if not obj.audience:
          obj.audience = act.audience
      obj.published = datetime.now(tz=timezone.utc)
      obj.updated = datetime.now(tz=timezone.utc)
      objects.append(obj)
    for obj in objects:
        await storage.get().store(obj)
    return objects


@rule("Add")
async def add(act: Activity):
    bus = Bus(act.actor)
    for target in act.target:
        collection = await bus.dereference(target)
        assert collection and "Collection" in collection.type or "OrderedCollection" in collection.type, f"Target is not a Collection: {collection!r}"
        assert await bus.can_write(collection), "Forbidden"
        for obj in act.object:
            await storage.get().add(collection.id, obj, refresh=True)