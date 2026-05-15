import pytest
from unittest.mock import MagicMock
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from krabs_domain.repositories.agent import SessionRepository
from krabs_domain.models.agent import Session


@pytest.fixture
def container(mocker):
    mock_client = mocker.patch("krabs_domain.repositories.base.CosmosClient")
    c = MagicMock()
    mock_client.from_connection_string.return_value \
        .get_database_client.return_value \
        .get_container_client.return_value = c
    return c


@pytest.fixture
def repo(container):
    return SessionRepository()


NUMBER = "+27821234567"


def _session_dict(**kwargs):
    return {"id": NUMBER, "whatsapp_number": NUMBER, "messages": [], **kwargs}


class TestGet:
    def test_returns_session_when_found(self, repo, container):
        container.read_item.return_value = _session_dict()
        assert repo.get(NUMBER).whatsapp_number == NUMBER

    def test_returns_none_when_not_found(self, repo, container):
        container.read_item.side_effect = CosmosResourceNotFoundError(message="not found")
        assert repo.get(NUMBER) is None

    def test_passes_correct_partition_key(self, repo, container):
        container.read_item.return_value = _session_dict()
        repo.get(NUMBER)
        container.read_item.assert_called_once_with(NUMBER, partition_key=NUMBER)


class TestSave:
    def test_sets_id_to_whatsapp_number(self, repo, container):
        session = Session(id="old-id", whatsapp_number=NUMBER)
        repo.save(session)
        assert session.id == NUMBER

    def test_calls_upsert(self, repo, container):
        repo.save(Session(id=NUMBER, whatsapp_number=NUMBER))
        container.upsert_item.assert_called_once()

    def test_returns_session(self, repo, container):
        session = Session(id=NUMBER, whatsapp_number=NUMBER)
        assert repo.save(session) is session

    def test_updates_updated_at(self, repo, container):
        session = Session(id=NUMBER, whatsapp_number=NUMBER)
        original = session.updated_at
        repo.save(session)
        assert session.updated_at >= original


class TestGetOrCreate:
    def test_returns_existing_session(self, repo, container):
        container.read_item.return_value = _session_dict()
        repo.get_or_create(NUMBER)
        container.upsert_item.assert_not_called()

    def test_creates_new_session_when_not_found(self, repo, container):
        container.read_item.side_effect = CosmosResourceNotFoundError(message="not found")
        session = repo.get_or_create(NUMBER)
        assert session.whatsapp_number == NUMBER
        container.upsert_item.assert_called_once()

    def test_new_session_has_correct_number(self, repo, container):
        container.read_item.side_effect = CosmosResourceNotFoundError(message="not found")
        session = repo.get_or_create(NUMBER)
        assert session.id == NUMBER
