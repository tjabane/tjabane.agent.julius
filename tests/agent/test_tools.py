from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from agent.tools import dispatch
from agent.tools.deps import ToolDeps
from models.knowledge import Memory, MemoryType, Skill
from models.reporting import Schedule, Frequency


# ── dispatch ──────────────────────────────────────────────────────────────────

class TestDispatch:
    def test_routes_to_correct_handler(self):
        mock_investec = MagicMock()
        mock_investec.get_accounts.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_accounts", {}, deps)

        mock_investec.get_accounts.assert_called_once()

    def test_raises_for_unknown_tool(self):
        with pytest.raises(ValueError, match="No handler for tool"):
            dispatch("nonexistent_tool", {})


# ── banking ───────────────────────────────────────────────────────────────────

class TestBankingTools:
    def test_get_accounts(self):
        mock_investec = MagicMock()
        mock_investec.get_accounts.return_value = [{"id": "123", "name": "Cheque"}]
        deps = ToolDeps(investec=mock_investec)

        result = dispatch("get_accounts", {}, deps)

        mock_investec.get_accounts.assert_called_once()
        assert "123" in result

    def test_get_balance(self):
        mock_investec = MagicMock()
        mock_investec.get_balance.return_value = {"current": 5000.0, "available": 4800.0}
        deps = ToolDeps(investec=mock_investec)

        result = dispatch("get_balance", {"account_id": "acc-1"}, deps)

        mock_investec.get_balance.assert_called_once_with("acc-1")
        assert "5000" in result

    def test_get_transactions_passes_all_filters(self):
        mock_investec = MagicMock()
        mock_investec.get_transactions.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_transactions", {
            "account_id": "acc-1",
            "from_date": "2024-01-01",
            "to_date": "2024-01-31",
            "transaction_type": "DEBIT",
            "include_pending": True,
        }, deps)

        mock_investec.get_transactions.assert_called_once_with(
            "acc-1",
            from_date="2024-01-01",
            to_date="2024-01-31",
            transaction_type="DEBIT",
            include_pending=True,
        )

    def test_get_transactions_defaults_optional_filters(self):
        mock_investec = MagicMock()
        mock_investec.get_transactions.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_transactions", {"account_id": "acc-1"}, deps)

        mock_investec.get_transactions.assert_called_once_with(
            "acc-1",
            from_date=None,
            to_date=None,
            transaction_type=None,
            include_pending=False,
        )

    def test_get_beneficiaries(self):
        mock_investec = MagicMock()
        mock_investec.get_beneficiaries.return_value = [{"beneficiaryId": "b1"}]
        mock_investec.get_beneficiary_categories.return_value = []
        deps = ToolDeps(investec=mock_investec)

        result = dispatch("get_beneficiaries", {}, deps)

        mock_investec.get_beneficiaries.assert_called_once()
        assert "b1" in result

    def test_get_documents_without_type(self):
        mock_investec = MagicMock()
        mock_investec.get_documents.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_documents", {"account_id": "acc-1", "from_date": "2024-01-01", "to_date": "2024-03-31"}, deps)

        mock_investec.get_documents.assert_called_once_with("acc-1", "2024-01-01", "2024-03-31")

    def test_get_documents_with_type_calls_get_document(self):
        mock_investec = MagicMock()
        mock_investec.get_document.return_value = {"content": "..."}
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_documents", {
            "account_id": "acc-1",
            "from_date": "2024-01-01",
            "to_date": "2024-03-31",
            "document_type": "statement",
            "document_date": "2024-02-01",
        }, deps)

        mock_investec.get_document.assert_called_once_with("acc-1", "statement", "2024-02-01")


# ── scheduling ────────────────────────────────────────────────────────────────

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


# ── reporting ─────────────────────────────────────────────────────────────────

class TestReportingTools:
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

        dispatch("send_email", {
            "subject": "Report",
            "body": "Content",
            "schedule_id": "sched-99",
        }, deps)

        saved = mock_repo.save.call_args[0][0]
        assert saved.schedule_id == "sched-99"

    def test_send_email_schedule_id_optional(self):
        mock_repo = MagicMock()
        mock_email = MagicMock()
        deps = ToolDeps(report_repo=mock_repo, email=mock_email)

        dispatch("send_email", {"subject": "Ad-hoc Report", "body": "Content"}, deps)

        saved = mock_repo.save.call_args[0][0]
        assert saved.schedule_id is None


# ── memory ────────────────────────────────────────────────────────────────────

class TestMemoryTools:
    def test_save_memory(self):
        mock_repo = MagicMock()
        deps = ToolDeps(memory_repo=mock_repo)

        result = dispatch("save_memory", {"type": "preference", "content": "prefers ZAR"}, deps)

        mock_repo.save.assert_called_once()
        saved = mock_repo.save.call_args[0][0]
        assert saved.type == MemoryType.PREFERENCE
        assert saved.content == "prefers ZAR"
        assert "saved" in result.lower()

    def test_search_memory_returns_matches(self):
        mock_repo = MagicMock()
        mock_repo.search.return_value = [Memory(type=MemoryType.FACT, content="lives in Cape Town")]
        deps = ToolDeps(memory_repo=mock_repo)

        result = dispatch("search_memory", {"keywords": ["location"]}, deps)

        mock_repo.search.assert_called_once_with(["location"])
        assert "Cape Town" in result

    def test_search_memory_empty(self):
        mock_repo = MagicMock()
        mock_repo.search.return_value = []
        deps = ToolDeps(memory_repo=mock_repo)

        result = dispatch("search_memory", {"keywords": ["xyz"]}, deps)

        assert "No relevant memories" in result


# ── skills ────────────────────────────────────────────────────────────────────

class TestSkillsTools:
    def test_save_skill(self):
        mock_repo = MagicMock()
        deps = ToolDeps(skill_repo=mock_repo)

        result = dispatch("save_skill", {
            "name": "weekly_report",
            "description": "How to generate weekly reports",
            "content": "# Weekly Report\nAlways include totals.",
        }, deps)

        mock_repo.save.assert_called_once()
        assert "weekly_report" in result

    def test_load_skill_found(self):
        skill = Skill(name="weekly_report", description="desc", content="# Instructions")
        mock_repo = MagicMock()
        mock_repo.get_by_name.return_value = skill
        deps = ToolDeps(skill_repo=mock_repo)

        result = dispatch("load_skill", {"name": "weekly_report"}, deps)

        assert "# Instructions" in result

    def test_load_skill_not_found(self):
        mock_repo = MagicMock()
        mock_repo.get_by_name.return_value = None
        deps = ToolDeps(skill_repo=mock_repo)

        result = dispatch("load_skill", {"name": "nonexistent"}, deps)

        assert "No skill found" in result

    def test_list_skills_empty(self):
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = []
        deps = ToolDeps(skill_repo=mock_repo)

        result = dispatch("list_skills", {}, deps)

        assert "No skills" in result

    def test_list_skills_returns_names(self):
        mock_repo = MagicMock()
        mock_repo.list_all.return_value = [
            Skill(name="weekly_report", description="Weekly reports", content="..."),
            Skill(name="transfer", description="How to transfer", content="..."),
        ]
        deps = ToolDeps(skill_repo=mock_repo)

        result = dispatch("list_skills", {}, deps)

        assert "weekly_report" in result
        assert "transfer" in result
