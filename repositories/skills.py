from datetime import datetime
from models.skill import Skill
from .base import BaseRepository


class SkillRepository(BaseRepository):
    def __init__(self):
        super().__init__("skills")

    def get_by_name(self, name: str) -> Skill | None:
        rows = self._query(
            "SELECT * FROM c WHERE c.name = @name",
            [{"name": "@name", "value": name}],
        )
        return Skill(**rows[0]) if rows else None

    def save(self, skill: Skill) -> Skill:
        skill.updated_at = datetime.utcnow()
        existing = self.get_by_name(skill.name)
        if existing:
            skill.id = existing.id
            skill.created_at = existing.created_at
        self._upsert(skill)
        return skill

    def list_all(self) -> list[Skill]:
        rows = self._query("SELECT * FROM c ORDER BY c.name")
        return [Skill(**r) for r in rows]

    def delete(self, skill_id: str) -> None:
        self._delete(skill_id, partition_key=skill_id)
