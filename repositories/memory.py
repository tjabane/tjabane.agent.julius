from datetime import datetime
from models.memory import Memory
from .base import BaseRepository


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
        rows = self._query(f"SELECT * FROM c WHERE {conditions}", parameters)
        results = [Memory(**r) for r in rows]
        now = datetime.utcnow()
        for m in results:
            m.last_referenced = now
            self._upsert(m)
        return results

    def delete(self, memory_id: str) -> None:
        self._delete(memory_id, partition_key=memory_id)
