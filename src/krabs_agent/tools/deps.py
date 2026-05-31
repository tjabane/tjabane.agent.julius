from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from krabs_domain.banking import BankingClient
    from krabs_domain.repositories.knowledge import MemoryRepository, SkillRepository
    from krabs_domain.repositories.reporting import ReportRepository, ScheduleRepository
    from krabs_services.communication.protocols import ReportSender


@dataclass
class ToolDeps:
    banking: BankingClient | None = None
    schedule_repo: ScheduleRepository | None = None
    report_repo: ReportRepository | None = None
    email: ReportSender | None = None
    memory_repo: MemoryRepository | None = None
    skill_repo: SkillRepository | None = None
