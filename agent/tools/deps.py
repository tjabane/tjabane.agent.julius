from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.investec_client import InvestecClient
    from services.email_service import EmailService
    from repositories.schedules import ScheduleRepository
    from repositories.reports import ReportRepository
    from repositories.memory import MemoryRepository
    from repositories.skills import SkillRepository


@dataclass
class ToolDeps:
    investec: InvestecClient | None = None
    schedule_repo: ScheduleRepository | None = None
    report_repo: ReportRepository | None = None
    email: EmailService | None = None
    memory_repo: MemoryRepository | None = None
    skill_repo: SkillRepository | None = None
