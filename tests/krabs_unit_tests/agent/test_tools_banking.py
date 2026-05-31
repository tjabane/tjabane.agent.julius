import pytest

from krabs_agent.tools import dispatch
from krabs_agent.tools.banking import DEFINITIONS
from krabs_agent.tools.deps import ToolDeps


class TestBankingTools:
    def test_no_tools_are_registered(self):
        assert DEFINITIONS == []

    def test_dispatch_rejects_unregistered_banking_tool(self):
        deps = ToolDeps()

        with pytest.raises(ValueError, match="No handler for tool"):
            dispatch("get_accounts", {}, deps)
