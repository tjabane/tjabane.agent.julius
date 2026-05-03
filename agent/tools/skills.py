from models.skill import Skill
from repositories.skills import SkillRepository

_repo: SkillRepository | None = None


def _get_repo() -> SkillRepository:
    global _repo
    if _repo is None:
        _repo = SkillRepository()
    return _repo


DEFINITIONS = [
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


def handle(tool_name: str, inputs: dict) -> str:
    repo = _get_repo()

    if tool_name == "save_skill":
        skill = Skill(name=inputs["name"], description=inputs["description"], content=inputs["content"])
        repo.save(skill)
        return f"Skill '{inputs['name']}' saved."

    if tool_name == "load_skill":
        skill = repo.get_by_name(inputs["name"])
        if not skill:
            return f"No skill found with name '{inputs['name']}'."
        return f"# Skill: {skill.name}\n\n{skill.content}"

    if tool_name == "list_skills":
        skills = repo.list_all()
        if not skills:
            return "No skills saved yet."
        return "\n".join(f"- **{s.name}**: {s.description}" for s in skills)

    raise ValueError(f"Unknown skill tool: {tool_name}")
