from __future__ import annotations
from typing import TYPE_CHECKING
from models.memory import Memory, MemoryType
from repositories.memory import MemoryRepository

if TYPE_CHECKING:
    from agent.tools.deps import ToolDeps

_repo: MemoryRepository | None = None


def _get_repo() -> MemoryRepository:
    global _repo
    if _repo is None:
        _repo = MemoryRepository()
    return _repo


DEFINITIONS = [
    {
        "name": "save_memory",
        "description": "Save a preference, habit, or fact about the user to persist across conversations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["preference", "habit", "fact"]},
                "content": {"type": "string", "description": "The memory to save"},
            },
            "required": ["type", "content"],
        },
    },
    {
        "name": "search_memory",
        "description": "Search stored memories by keywords to retrieve relevant preferences or facts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to search for",
                }
            },
            "required": ["keywords"],
        },
    },
]


def handle(tool_name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    repo = (deps.memory_repo if deps and deps.memory_repo else None) or _get_repo()

    if tool_name == "save_memory":
        memory = Memory(type=MemoryType(inputs["type"]), content=inputs["content"])
        repo.save(memory)
        return f"Memory saved: {inputs['content']}"

    if tool_name == "search_memory":
        results = repo.search(inputs["keywords"])
        if not results:
            return "No relevant memories found."
        return "\n".join(f"[{m.type.value}] {m.content}" for m in results)

    raise ValueError(f"Unknown memory tool: {tool_name}")
