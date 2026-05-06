from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from julius_services.investec_client import InvestecClient
    from julius_services.email_service import EmailService
    from julius_domain.repositories.reporting import ScheduleRepository, ReportRepository
    from julius_domain.repositories.knowledge import MemoryRepository, SkillRepository


@dataclass
class ToolDeps:
    investec: InvestecClient | None = None
    schedule_repo: ScheduleRepository | None = None
    report_repo: ReportRepository | None = None
    email: EmailService | None = None
    memory_repo: MemoryRepository | None = None
    skill_repo: SkillRepository | None = None
