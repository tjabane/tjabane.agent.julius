# Code Quality Standards

This project uses a local Codex skill and repo tooling to keep Python code aligned with Clean Code, Clean Architecture, and Python naming standards.

## Codex Skill

Use the `python-clean-architecture-review` skill when writing or reviewing Python code in this repo.

The skill checks for:

- explicit dependency injection at composition boundaries;
- clear Clean Architecture layer ownership;
- Clean Code naming, function size, parameter shape, and error handling;
- idiomatic Python naming and type-hint usage;
- tool-calling separation between model loop, schemas, dispatcher, and dependencies.

## Local Quality Commands

Run these before committing Python changes:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
```

To apply mechanical formatting:

```powershell
uv run ruff format .
uv run ruff check . --fix
```

Review all fixes before committing. Do not rely on automated fixes for design quality.

## Current Baseline

The linter and type checker are configured, but the existing codebase does not yet pass all checks. Treat failures as cleanup work, not as permission to lower the quality bar.
