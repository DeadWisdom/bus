from fastapi.testclient import TestClient


def test_put(client: TestClient):
    r = client.put("/test", json={"type": "Thing"})
    assert r.status_code == 201
    obj = r.json()
    assert obj['@context'] == "https://www.w3.org/ns/activitystreams"
    assert obj["id"] == "http://testserver/test"
    assert obj["type"] == "Thing"
    assert obj["attributedTo"] == "https://brantley.dev"
    assert obj['published']
    assert obj['updated']
  

def test_get(client: TestClient):
    client.put("/test", json={"type": "Thing"})
    r = client.get("/test")
    assert r.status_code == 200
    obj = r.json()
    assert obj["id"] == "http://testserver/test"
    assert obj["type"] == "Thing"
    assert obj["attributedTo"] == "https://brantley.dev"
  

def test_put_anon(client: TestClient):
    r = client.put("/test", json={"type": "Thing"}, headers={"Authorization": ""})
    assert r.status_code == 401


def test_get_private(client: TestClient):
    r = client.put("/private", json={"type": "Collection", "audience": "me"})
    r = client.get("/private", headers={"Authorization": ""})
    assert r.status_code == 403

    r = client.put("/private/thing", json={"type": "Thing"})
    r = client.get("/private/thing", headers={"Authorization": ""})
    assert r.status_code == 403


def test_get_public(client: TestClient):
    r = client.put("/public", json={"type": "Thing", "audience": "Public"})
    r = client.get("/public", headers={"Authorization": ""})
    assert r.status_code == 200

    r = client.put("/public", json={"type": "Thing"})
    r = client.get("/public", headers={"Authorization": ""})
    assert r.status_code == 403
