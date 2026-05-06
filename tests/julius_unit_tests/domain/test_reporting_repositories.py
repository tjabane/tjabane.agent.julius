import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, call
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from julius_domain.repositories.reporting import ScheduleRepository, ReportRepository
from julius_domain.models.reporting import Schedule, Frequency, Report


@pytest.fixture
def container(mocker):
    mock_client = mocker.patch("julius_domain.repositories.base.CosmosClient")
    c = MagicMock()
    mock_client.from_connection_string.return_value \
        .get_database_client.return_value \
        .get_container_client.return_value = c
    return c


@pytest.fixture
def schedule_repo(container):
    return ScheduleRepository()


@pytest.fixture
def report_repo(container):
    return ReportRepository()


def _schedule_dict(**kwargs):
    base = {
        "id": "sched-1",
        "query": "monthly summary",
        "frequency": "daily",
        "next_run": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**base, **kwargs}


def _report_dict(**kwargs):
    base = {
        "id": "report-1",
        "query": "spending summary",
        "content": "You spent R1000",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**base, **kwargs}


class TestScheduleRepositoryGet:
    def test_returns_schedule_when_found(self, schedule_repo, container):
        container.read_item.return_value = _schedule_dict()
        schedule = schedule_repo.get("sched-1")
        assert schedule.id == "sched-1"

    def test_returns_none_when_not_found(self, schedule_repo, container):
        container.read_item.side_effect = CosmosResourceNotFoundError(message="not found")
        assert schedule_repo.get("sched-1") is None

    def test_passes_correct_partition_key(self, schedule_repo, container):
        container.read_item.return_value = _schedule_dict()
        schedule_repo.get("sched-1")
        container.read_item.assert_called_once_with("sched-1", partition_key="sched-1")


class TestScheduleRepositorySave:
    def test_calls_upsert(self, schedule_repo, container):
        schedule = Schedule(query="q", frequency=Frequency.DAILY, next_run=datetime.now(timezone.utc))
        schedule_repo.save(schedule)
        container.upsert_item.assert_called_once()

    def test_returns_schedule(self, schedule_repo, container):
        schedule = Schedule(query="q", frequency=Frequency.DAILY, next_run=datetime.now(timezone.utc))
        assert schedule_repo.save(schedule) is schedule

    def test_updates_updated_at(self, schedule_repo, container):
        schedule = Schedule(query="q", frequency=Frequency.DAILY, next_run=datetime.now(timezone.utc))
        original = schedule.updated_at
        schedule_repo.save(schedule)
        assert schedule.updated_at >= original


class TestScheduleRepositoryDelete:
    def test_calls_delete_with_correct_args(self, schedule_repo, container):
        schedule_repo.delete("sched-1")
        container.delete_item.assert_called_once_with("sched-1", partition_key="sched-1")

    def test_silences_not_found(self, schedule_repo, container):
        container.delete_item.side_effect = CosmosResourceNotFoundError(message="not found")
        schedule_repo.delete("sched-1")


class TestScheduleRepositoryListAll:
    def test_returns_all_schedules(self, schedule_repo, container):
        container.query_items.return_value = [_schedule_dict(id="a"), _schedule_dict(id="b")]
        result = schedule_repo.list_all()
        assert len(result) == 2

    def test_returns_empty_list(self, schedule_repo, container):
        container.query_items.return_value = []
        assert schedule_repo.list_all() == []

    def test_uses_correct_query(self, schedule_repo, container):
        container.query_items.return_value = []
        schedule_repo.list_all()
        query = container.query_items.call_args.kwargs["query"]
        assert "SELECT" in query


class TestScheduleRepositoryListDue:
    def test_returns_due_schedules(self, schedule_repo, container):
        container.query_items.return_value = [_schedule_dict()]
        result = schedule_repo.list_due()
        assert len(result) == 1

    def test_passes_now_as_parameter(self, schedule_repo, container):
        container.query_items.return_value = []
        schedule_repo.list_due()
        params = container.query_items.call_args.kwargs["parameters"]
        assert any(p["name"] == "@now" for p in params)

    def test_query_filters_by_enabled_and_next_run(self, schedule_repo, container):
        container.query_items.return_value = []
        schedule_repo.list_due()
        query = container.query_items.call_args.kwargs["query"]
        assert "enabled" in query
        assert "next_run" in query


class TestReportRepositorySave:
    def test_calls_upsert(self, report_repo, container):
        report = Report(query="q", content="c")
        report_repo.save(report)
        container.upsert_item.assert_called_once()

    def test_returns_report(self, report_repo, container):
        report = Report(query="q", content="c")
        assert report_repo.save(report) is report


class TestReportRepositoryListRecent:
    def test_returns_reports(self, report_repo, container):
        container.query_items.return_value = [_report_dict(), _report_dict(id="report-2")]
        assert len(report_repo.list_recent()) == 2

    def test_default_limit_is_10(self, report_repo, container):
        container.query_items.return_value = []
        report_repo.list_recent()
        query = container.query_items.call_args.kwargs["query"]
        assert "TOP 10" in query

    def test_respects_custom_limit(self, report_repo, container):
        container.query_items.return_value = []
        report_repo.list_recent(limit=5)
        query = container.query_items.call_args.kwargs["query"]
        assert "TOP 5" in query

    def test_orders_by_created_at_desc(self, report_repo, container):
        container.query_items.return_value = []
        report_repo.list_recent()
        query = container.query_items.call_args.kwargs["query"]
        assert "created_at DESC" in query
