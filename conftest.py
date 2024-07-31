import pytest, logging
from fastapi.testclient import TestClient
from valet.app import app
from valet.auth import mint_token
from valet.models import Account

@pytest.fixture(autouse=True, scope="function")
def storage(caplog):
    from valet.bus.base import storage, ElasticStorage
    ElasticStorage.reset_testing()
    token = storage.set(ElasticStorage(prefix="testing-"))
    with caplog.at_level(logging.CRITICAL, logger="elastic_transport.transport"):
        yield
    storage.get().close()
    storage.reset(token)

@pytest.fixture()
def client(users):
    token = mint_token(users['/accounts/brantley'])
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client

@pytest.fixture()
def users(monkeypatch):
    accounts = {
        '/accounts/brantley': Account(
            id='/accounts/brantley',
            name='Brantley Harris',
            oauth='google/106488577930653701349',
            email="deadwisdom@gmail.com",
            image="https://lh3.googleusercontent.com/a/ACg8ocKnqEJjbrI27meG33hDbquxjznTod5cTO1e0YfagahZfHZ910d6=s96-c")
    }
    async def load_account(id):
        return accounts.get(id)
    monkeypatch.setattr('valet.auth.load_account', load_account)
    return accounts
# 