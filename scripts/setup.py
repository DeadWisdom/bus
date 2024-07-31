import asyncio, os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


if __name__ == '__main__':
    from valet.bus.storage.elastic import ElasticStorage

    print("Setting up storage...")

    for prefix in ("", "testing-"):
        storage = ElasticStorage(prefix=prefix)
        asyncio.run(storage.setup())

    print("Done.")
