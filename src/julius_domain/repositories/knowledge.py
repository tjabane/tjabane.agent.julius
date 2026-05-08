from datetime import datetime, timezone
from julius_domain.models.knowledge import Memory, Skill
from .base import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MemoryRepository(BaseRepository):
    def __init__(self):
        super().__init__("memory")

    def save(self, memory: Memory) -> Memory:
        self._upsert(memory)
        return memory

    def list_all(self) -> list[Memory]:
        rows = self._query("SELECT * FROM c ORDER BY c.last_referenced DESC")
        return [Memory(**r) for r in rows]

    def search(self, keywords: list[str]) -> list[Memory]:
        conditions = " OR ".join(
            f"CONTAINS(LOWER(c.content), LOWER(@kw{i}))" for i, _ in enumerate(keywords)
        )
        parameters = [{"name": f"@kw{i}", "value": kw} for i, kw in enumerate(keywords)]
        rows = self._query(f"SELECT * FROM c WHERE {conditions}", parameters)  # nosec B608 - conditions contains only parameterized placeholder names, values are passed separately
        results = [Memory(**r) for r in rows]
        now = _utcnow()
        for m in results:
            m.last_referenced = now
            self._upsert(m)
        return results

    def delete(self, memory_id: str) -> None:
        self._delete(memory_id, partition_key=memory_id)


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
        skill.updated_at = _utcnow()
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
