from models.memory import Memory, MemoryType
from repositories.memory import MemoryRepository

_repo = MemoryRepository()

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


def handle(tool_name: str, inputs: dict) -> str:
    if tool_name == "save_memory":
        memory = Memory(type=MemoryType(inputs["type"]), content=inputs["content"])
        _repo.save(memory)
        return f"Memory saved: {inputs['content']}"

    if tool_name == "search_memory":
        results = _repo.search(inputs["keywords"])
        if not results:
            return "No relevant memories found."
        return "\n".join(f"[{m.type.value}] {m.content}" for m in results)

    raise ValueError(f"Unknown memory tool: {tool_name}")
