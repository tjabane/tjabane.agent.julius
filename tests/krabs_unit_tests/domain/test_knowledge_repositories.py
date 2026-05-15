import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from krabs_domain.repositories.knowledge import MemoryRepository, SkillRepository
from krabs_domain.models.knowledge import Memory, MemoryType, Skill


@pytest.fixture
def container(mocker):
    mock_client = mocker.patch("krabs_domain.repositories.base.CosmosClient")
    c = MagicMock()
    mock_client.from_connection_string.return_value \
        .get_database_client.return_value \
        .get_container_client.return_value = c
    return c


@pytest.fixture
def memory_repo(container):
    return MemoryRepository()


@pytest.fixture
def skill_repo(container):
    return SkillRepository()


def _memory_dict(**kwargs):
    base = {
        "id": "mem-1",
        "type": "fact",
        "content": "User prefers ZAR",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_referenced": datetime.now(timezone.utc).isoformat(),
    }
    return {**base, **kwargs}


def _skill_dict(**kwargs):
    base = {
        "id": "skill-1",
        "name": "monthly_summary",
        "description": "Monthly spending summary",
        "content": "Show me all transactions this month",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**base, **kwargs}


class TestMemoryRepositorySave:
    def test_calls_upsert(self, memory_repo, container):
        memory = Memory(type=MemoryType.FACT, content="test fact")
        memory_repo.save(memory)
        container.upsert_item.assert_called_once()

    def test_returns_memory(self, memory_repo, container):
        memory = Memory(type=MemoryType.FACT, content="test fact")
        assert memory_repo.save(memory) is memory


class TestMemoryRepositoryListAll:
    def test_returns_all_memories(self, memory_repo, container):
        container.query_items.return_value = [_memory_dict(), _memory_dict(id="mem-2")]
        assert len(memory_repo.list_all()) == 2

    def test_returns_empty_list(self, memory_repo, container):
        container.query_items.return_value = []
        assert memory_repo.list_all() == []

    def test_orders_by_last_referenced(self, memory_repo, container):
        container.query_items.return_value = []
        memory_repo.list_all()
        query = container.query_items.call_args.kwargs["query"]
        assert "last_referenced" in query


class TestMemoryRepositorySearch:
    def test_returns_matching_memories(self, memory_repo, container):
        container.query_items.return_value = [_memory_dict()]
        results = memory_repo.search(["ZAR"])
        assert len(results) == 1

    def test_builds_parameterized_query_for_each_keyword(self, memory_repo, container):
        container.query_items.return_value = []
        memory_repo.search(["ZAR", "budget"])
        params = container.query_items.call_args.kwargs["parameters"]
        names = [p["name"] for p in params]
        assert "@kw0" in names
        assert "@kw1" in names

    def test_keyword_values_passed_as_parameters(self, memory_repo, container):
        container.query_items.return_value = []
        memory_repo.search(["ZAR"])
        params = container.query_items.call_args.kwargs["parameters"]
        assert params[0]["value"] == "ZAR"

    def test_updates_last_referenced_on_results(self, memory_repo, container):
        container.query_items.return_value = [_memory_dict()]
        results = memory_repo.search(["ZAR"])
        assert container.upsert_item.call_count == len(results)

    def test_returns_empty_list_when_no_matches(self, memory_repo, container):
        container.query_items.return_value = []
        assert memory_repo.search(["unknown"]) == []


class TestMemoryRepositoryDelete:
    def test_calls_delete_with_correct_args(self, memory_repo, container):
        memory_repo.delete("mem-1")
        container.delete_item.assert_called_once_with("mem-1", partition_key="mem-1")

    def test_silences_not_found(self, memory_repo, container):
        container.delete_item.side_effect = CosmosResourceNotFoundError(message="not found")
        memory_repo.delete("mem-1")


class TestSkillRepositoryGetByName:
    def test_returns_skill_when_found(self, skill_repo, container):
        container.query_items.return_value = [_skill_dict()]
        skill = skill_repo.get_by_name("monthly_summary")
        assert skill.name == "monthly_summary"

    def test_returns_none_when_not_found(self, skill_repo, container):
        container.query_items.return_value = []
        assert skill_repo.get_by_name("missing") is None

    def test_queries_by_name_parameter(self, skill_repo, container):
        container.query_items.return_value = []
        skill_repo.get_by_name("monthly_summary")
        params = container.query_items.call_args.kwargs["parameters"]
        assert params[0] == {"name": "@name", "value": "monthly_summary"}


class TestSkillRepositorySave:
    def test_creates_new_skill(self, skill_repo, container):
        container.query_items.return_value = []
        skill = Skill(name="new_skill", description="desc", content="content")
        skill_repo.save(skill)
        container.upsert_item.assert_called_once()

    def test_preserves_id_for_existing_skill(self, skill_repo, container):
        existing = _skill_dict(id="existing-id")
        container.query_items.return_value = [existing]
        skill = Skill(name="monthly_summary", description="desc", content="content")
        skill_repo.save(skill)
        assert skill.id == "existing-id"

    def test_preserves_created_at_for_existing_skill(self, skill_repo, container):
        original_created = datetime(2024, 1, 1, tzinfo=timezone.utc)
        existing = _skill_dict(created_at=original_created.isoformat())
        container.query_items.return_value = [existing]
        skill = Skill(name="monthly_summary", description="desc", content="content")
        skill_repo.save(skill)
        assert skill.created_at == original_created

    def test_returns_skill(self, skill_repo, container):
        container.query_items.return_value = []
        skill = Skill(name="new_skill", description="desc", content="content")
        assert skill_repo.save(skill) is skill


class TestSkillRepositoryListAll:
    def test_returns_all_skills(self, skill_repo, container):
        container.query_items.return_value = [_skill_dict(), _skill_dict(id="skill-2", name="other")]
        assert len(skill_repo.list_all()) == 2

    def test_orders_by_name(self, skill_repo, container):
        container.query_items.return_value = []
        skill_repo.list_all()
        query = container.query_items.call_args.kwargs["query"]
        assert "c.name" in query


class TestSkillRepositoryDelete:
    def test_calls_delete_with_correct_args(self, skill_repo, container):
        skill_repo.delete("skill-1")
        container.delete_item.assert_called_once_with("skill-1", partition_key="skill-1")

    def test_silences_not_found(self, skill_repo, container):
        container.delete_item.side_effect = CosmosResourceNotFoundError(message="not found")
        skill_repo.delete("skill-1")
