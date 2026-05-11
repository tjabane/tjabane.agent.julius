from unittest.mock import MagicMock
from julius_agent.tools import dispatch
from julius_agent.tools.deps import ToolDeps
from julius_domain.models.knowledge import Memory, MemoryType, Skill


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
