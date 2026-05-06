from datetime import datetime, timezone
from unittest.mock import MagicMock
from agent.tools import dispatch
from agent.tools.deps import ToolDeps
from models.reporting import Schedule, Frequency


class TestSchedulingTools:
    def test_list_empty(self):
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = []
        deps = ToolDeps(schedule_repo=mock_repo)

        result = dispatch("manage_schedule", {"action": "list"}, deps)

        assert result == "No schedules configured."

    def test_list_returns_schedule_summary(self):
        schedule = Schedule(query="balance report", frequency=Frequency.DAILY, next_run=datetime.now(timezone.utc))
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = [schedule]
        deps = ToolDeps(schedule_repo=mock_repo)

        result = dispatch("manage_schedule", {"action": "list"}, deps)

        assert "balance report" in result
        assert "daily" in result

    def test_create_saves_and_returns_id(self):
        mock_repo = MagicMock()
        deps = ToolDeps(schedule_repo=mock_repo)

        result = dispatch("manage_schedule", {
            "action": "create",
            "query": "send weekly summary",
            "frequency": "weekly",
        }, deps)

        mock_repo.save.assert_called_once()
        assert "created" in result.lower()

    def test_update_not_found(self):
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        deps = ToolDeps(schedule_repo=mock_repo)

        result = dispatch("manage_schedule", {"action": "update", "schedule_id": "missing"}, deps)

        assert "not found" in result.lower()

    def test_enable_sets_flag(self):
        schedule = Schedule(query="q", frequency=Frequency.DAILY, next_run=datetime.now(timezone.utc), enabled=False)
        mock_repo = MagicMock()
        mock_repo.get.return_value = schedule
        deps = ToolDeps(schedule_repo=mock_repo)

        dispatch("manage_schedule", {"action": "enable", "schedule_id": schedule.id}, deps)

        saved = mock_repo.save.call_args[0][0]
        assert saved.enabled is True

    def test_disable_sets_flag(self):
        schedule = Schedule(query="q", frequency=Frequency.DAILY, next_run=datetime.now(timezone.utc), enabled=True)
        mock_repo = MagicMock()
        mock_repo.get.return_value = schedule
        deps = ToolDeps(schedule_repo=mock_repo)

        dispatch("manage_schedule", {"action": "disable", "schedule_id": schedule.id}, deps)

        saved = mock_repo.save.call_args[0][0]
        assert saved.enabled is False

    def test_delete_calls_repo(self):
        mock_repo = MagicMock()
        deps = ToolDeps(schedule_repo=mock_repo)

        dispatch("manage_schedule", {"action": "delete", "schedule_id": "sched-1"}, deps)

        mock_repo.delete.assert_called_once_with("sched-1")


class TestEmailTools:
    def test_send_email_saves_report_and_sends(self):
        mock_repo = MagicMock()
        mock_email = MagicMock()
        deps = ToolDeps(report_repo=mock_repo, email=mock_email)

        dispatch("send_email", {"subject": "Monthly Report", "body": "Balance: R5000"}, deps)

        mock_repo.save.assert_called_once()
        mock_email.send_report.assert_called_once_with(subject="Monthly Report", body="Balance: R5000")

    def test_send_email_stores_schedule_id(self):
        mock_repo = MagicMock()
        mock_email = MagicMock()
        deps = ToolDeps(report_repo=mock_repo, email=mock_email)

        dispatch("send_email", {"subject": "Report", "body": "Content", "schedule_id": "sched-99"}, deps)

        saved = mock_repo.save.call_args[0][0]
        assert saved.schedule_id == "sched-99"

    def test_send_email_schedule_id_optional(self):
        mock_repo = MagicMock()
        mock_email = MagicMock()
        deps = ToolDeps(report_repo=mock_repo, email=mock_email)

        dispatch("send_email", {"subject": "Ad-hoc Report", "body": "Content"}, deps)

        saved = mock_repo.save.call_args[0][0]
        assert saved.schedule_id is None
