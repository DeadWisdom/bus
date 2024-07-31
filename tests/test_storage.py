import pytest
import pytest_asyncio 

from valet.bus.storage.elastic import ElasticStorage, Query #, SearchResults
from valet.bus import Object


def ids(objects: list[Object]) -> set[str]:
    return set(item.id for item in objects)


@pytest_asyncio.fixture
async def storage():
    ElasticStorage.reset_testing()
    storage = ElasticStorage(prefix="testing-")
    yield storage
    await storage.aclose()


@pytest.mark.asyncio
async def test_store(storage: ElasticStorage):
    thing = Object(id="test", type="Thing")

    assert await storage.store(thing, refresh=True) == thing
    assert await storage.load("test") == thing


@pytest.mark.asyncio
async def test_add(storage: ElasticStorage):
    items = [Object(id=f"tests/{i}", type="Thing") for i in range(5)]
    for item in items:
        await storage.add("tests", item, refresh=True)
    
    query = Query(collection="tests")
    results = await storage.search(query)
    assert results.total == 5
    assert results.hits == items
    assert ids(results) == ids(items)


@pytest.mark.asyncio
async def test_remove(storage: ElasticStorage):
    items = [Object(id=f"tests/{i}", type="Thing") for i in range(5)]
    for item in items:
        await storage.add("tests", item, refresh=True)
    
    query = Query(collection="tests")
    while items:
        item = items.pop(0)
        await storage.remove("tests", id=item.id, refresh=True)
        results = await storage.search(query)
        assert results.total == len(items)
        assert ids(results) == ids(items)

    await storage.remove("tests", id="not in here", refresh=True)

@pytest.mark.asyncio
async def test_none(storage):
    assert await storage.load("nothing") is None
    
