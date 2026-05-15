from __future__ import annotations
from typing import TYPE_CHECKING
from krabs_domain.models.knowledge import Memory, MemoryType, Skill
from krabs_domain.repositories.knowledge import MemoryRepository, SkillRepository

if TYPE_CHECKING:
    from krabs_agent.tools.deps import ToolDeps

_memory_repo: MemoryRepository | None = None
_skill_repo: SkillRepository | None = None


def _get_memory_repo() -> MemoryRepository:
    global _memory_repo
    if _memory_repo is None:
        _memory_repo = MemoryRepository()
    return _memory_repo


def _get_skill_repo() -> SkillRepository:
    global _skill_repo
    if _skill_repo is None:
        _skill_repo = SkillRepository()
    return _skill_repo


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
    {
        "name": "save_skill",
        "description": "Save or update a markdown instruction file that teaches you how to approach a specific task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short identifier for the skill, e.g. 'weekly_report'"},
                "description": {"type": "string", "description": "One-line summary of what the skill covers"},
                "content": {"type": "string", "description": "Markdown instructions for the skill"},
            },
            "required": ["name", "description", "content"],
        },
    },
    {
        "name": "load_skill",
        "description": "Load a skill by name to guide how you approach a task. Call this before working on tasks with a matching skill.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The skill name to load"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "list_skills",
        "description": "List all available skills.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def handle(tool_name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    if tool_name == "save_memory":
        repo = (deps.memory_repo if deps and deps.memory_repo else None) or _get_memory_repo()
        memory = Memory(type=MemoryType(inputs["type"]), content=inputs["content"])
        repo.save(memory)
        return f"Memory saved: {inputs['content']}"

    if tool_name == "search_memory":
        repo = (deps.memory_repo if deps and deps.memory_repo else None) or _get_memory_repo()
        results = repo.search(inputs["keywords"])
        if not results:
            return "No relevant memories found."
        return "\n".join(f"[{m.type.value}] {m.content}" for m in results)

    if tool_name == "save_skill":
        repo = (deps.skill_repo if deps and deps.skill_repo else None) or _get_skill_repo()
        skill = Skill(name=inputs["name"], description=inputs["description"], content=inputs["content"])
        repo.save(skill)
        return f"Skill '{inputs['name']}' saved."

    if tool_name == "load_skill":
        repo = (deps.skill_repo if deps and deps.skill_repo else None) or _get_skill_repo()
        skill = repo.get_by_name(inputs["name"])
        if not skill:
            return f"No skill found with name '{inputs['name']}'."
        return f"# Skill: {skill.name}\n\n{skill.content}"

    if tool_name == "list_skills":
        repo = (deps.skill_repo if deps and deps.skill_repo else None) or _get_skill_repo()
        skills = repo.list_all()
        if not skills:
            return "No skills saved yet."
        return "\n".join(f"- **{s.name}**: {s.description}" for s in skills)

    raise ValueError(f"Unknown knowledge tool: {tool_name}")
