from fastapi.testclient import TestClient

def test_collection(client: TestClient):
    r = client.put("/brantley/notes", json={"type": "Collection", "audience": "Public"})
    r.raise_for_status()
    r = client.get("/brantley/notes")
    r.raise_for_status()

    r = client.put("/brantley/notes/1", json={"type": "Note", "content": "Hello, world!"})
    r.raise_for_status()

    r = client.get("/brantley/notes")
    r.raise_for_status()
    note = r.json()
    assert note["type"] == "Collection"
    assert note["totalItems"] == 1
    assert note["items"][0]["content"] == "Hello, world!"

    ### Get the note
    r = client.get("/brantley/notes/1")
    r.raise_for_status()

    note = r.json()
    assert note["type"] == "Note"
    assert note["content"] == "Hello, world!"