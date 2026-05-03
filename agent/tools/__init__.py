from __future__ import annotations
from typing import TYPE_CHECKING
from agent.tools import banking, knowledge, reporting

if TYPE_CHECKING:
    from agent.tools.deps import ToolDeps

_RAW_DEFINITIONS = (
    banking.DEFINITIONS
    + knowledge.DEFINITIONS
    + reporting.DEFINITIONS
)

ALL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t.get("input_schema", {"type": "object", "properties": {}, "required": []}),
        },
    }
    for t in _RAW_DEFINITIONS
]

_HANDLERS = {
    **{t["name"]: banking.handle for t in banking.DEFINITIONS},
    **{t["name"]: knowledge.handle for t in knowledge.DEFINITIONS},
    **{t["name"]: reporting.handle for t in reporting.DEFINITIONS},
}


def dispatch(tool_name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    handler = _HANDLERS.get(tool_name)
    if not handler:
        raise ValueError(f"No handler for tool: {tool_name}")
    return handler(tool_name, inputs, deps)
