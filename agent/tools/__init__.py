from __future__ import annotations
from typing import TYPE_CHECKING
from . import banking, scheduling, reporting, memory, skills

if TYPE_CHECKING:
    from agent.tools.deps import ToolDeps

_RAW_DEFINITIONS = (
    banking.DEFINITIONS
    + scheduling.DEFINITIONS
    + reporting.DEFINITIONS
    + memory.DEFINITIONS
    + skills.DEFINITIONS
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
    **{t["name"]: scheduling.handle for t in scheduling.DEFINITIONS},
    **{t["name"]: reporting.handle for t in reporting.DEFINITIONS},
    **{t["name"]: memory.handle for t in memory.DEFINITIONS},
    **{t["name"]: skills.handle for t in skills.DEFINITIONS},
}


def dispatch(tool_name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    handler = _HANDLERS.get(tool_name)
    if not handler:
        raise ValueError(f"No handler for tool: {tool_name}")
    return handler(tool_name, inputs, deps)
