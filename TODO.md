# V1 Manual Reporting Todo

## Goal

Ship manual, on-demand financial reports for v1 without reintroducing scheduled report execution.

## Todo

1. Define the minimum report workflow - done
   - V1 reports are manual spending scoreboards for daily, weekly, and period-based requests.
   - The agent generates report content from existing banking and datetime tools.
   - V1 returns the scoreboard in WhatsApp. Email/report storage can come later.

2. Add reporting tools using the current tool architecture - later
   - Do not add a report-generation tool for v1; the agent should compose the scoreboard from banking/date tool results.
   - Add `krabs_tools/schema/reporting.py` only when email delivery or report storage becomes a tool.
   - Add `krabs_tools/tools/reporting.py` or `krabs_tools/tools/reporting/` only when delivery/storage is required.
   - Add `create_reporting_tools(...)` only when those reporting tools exist.

3. Inject reporting dependencies explicitly
   - Use `ReportRepository` for saving report records if saving is part of v1.
   - Use `ReportSender` for email delivery if emailing is part of v1.
   - Keep concrete email/repository creation at composition boundaries.

4. Add focused tests
   - Schema validation tests.
   - Reporting tool behavior tests.
   - Factory registration tests.
   - Agent/tool registry integration tests if needed.

5. Update prompt and docs
   - Tell the agent it can generate manual spending scoreboard reports.
   - Make clear that recurring scheduled reports are not supported in v1.

6. Verify
   - Run focused reporting tests.
   - Run full test suite.
   - Run pyright.
   - Run Ruff on changed files.
