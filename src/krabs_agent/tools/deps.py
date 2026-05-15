from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from krabs_services.finance.investec_client import InvestecClient
    from krabs_services.communication.protocols import ReportSender
    from krabs_domain.repositories.reporting import ScheduleRepository, ReportRepository
    from krabs_domain.repositories.knowledge import MemoryRepository, SkillRepository


@dataclass
class ToolDeps:
    investec: InvestecClient | None = None
    schedule_repo: ScheduleRepository | None = None
    report_repo: ReportRepository | None = None
    email: ReportSender | None = None
    memory_repo: MemoryRepository | None = None
    skill_repo: SkillRepository | None = None
