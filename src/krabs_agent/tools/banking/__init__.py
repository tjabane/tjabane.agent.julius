from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from krabs_agent.tools.deps import ToolDeps

DEFINITIONS: list[dict[str, Any]] = []


def handle(tool_name: str, inputs: dict[str, Any], deps: ToolDeps | None = None) -> str:
    _ = (inputs, deps)
    raise ValueError(f"No banking tools are currently registered: {tool_name}")
