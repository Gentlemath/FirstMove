# First Move

## Build Your Daily Momentum

**First Move** is an AI work companion that helps independent workers build daily momentum by generating a focused work environment from calendar constraints and user-stated goals, then helping them start work quickly, stay oriented during the day, and end with a clear summary of progress.

### What First Move is (and is not)

First Move is **not** a to-do list, a daily planner, or an autonomous agent. Instead, it combines fixed calendar context with user-provided goals to prepare a focused daily environment with the right links, task-start cues, and lightweight momentum support. The goal is not to organize every task in life—it's to reduce startup friction, protect attention, and help users move from intention to action.

### Core Product Promise

- **Reduce attention fragmentation** by showing only what matters today.
- **Lower activation energy** by making the first step of each task obvious.
- **Prepare the right work context** without taking control away from the user.
- **Help users build daily momentum** and close the day with a supportive summary and explicit carry-forward items.

### Product Principles

- Prepare the stage; do not perform the work.
- Be a helper, not a planner.
- Today view should be regenerated daily, not endlessly accumulated.
- Suggestions should be short, useful, and encouraging, never intrusive.
- Attention support should feel constructive, calm, and non-judgmental.

### Target Users

Primary users are independent professionals, solo operators, founders, researchers, builders, students, analysts, and other knowledge workers who manage themselves. They want to do the work personally but need help with focus, setup, momentum, and small hints that make starting easier.

---
## Main folders
- `docs/` product spec, graphs, notes
- `frontend/` UI prototype
- `backend/` API and LLM logic

## Development workflow

### 1. Versioning
- Backend version source: `backend/app/__init__.py` contains `__version__`.
- Frontend version source: `frontend/package.json` `version` field.
- Check versions with `./scripts/show-version.sh`.

### 2. Changelog
- Use `CHANGELOG.md` with `## [Unreleased]` for ongoing work.
- On release, add a version entry (e.g. `## [0.1.0] - YYYY-MM-DD`) and move content.

### 3. Local setup (CI parity)
1. Install backend dependencies:
   - `python -m pip install --upgrade pip`
   - `pip install -r backend/requirements.txt`
   - `pip install pytest ruff mypy`
2. Setup frontend dependencies:
   - `cd frontend && npm ci`
3. Optional pre-commit:
   - `pip install pre-commit`
   - `pre-commit install`

### 4. Run tests locally
- Backend: `cd backend && pytest -q`
- External backend smoke tests: `cd backend && RUN_EXTERNAL_TESTS=1 pytest -q`
- Lint: `ruff check backend/app backend/tests`
- Typecheck: `mypy backend/app`
- Frontend: `cd frontend && npm run build`

Backend tests that require a real Google Calendar token, a live vLLM endpoint, or other machine-local setup are skipped unless `RUN_EXTERNAL_TESTS=1` is set.

### 5. GitHub Actions CI
- Workflow file: `.github/workflows/ci.yml`
- Trigger: on `push` and `pull_request` to `main`
- Jobs:
  - `backend`: install Python dependencies, run tests/lint/mypy
  - `frontend`: install Node dependencies, run build, and run lint if a lint script exists

### 6. Push protection (secret safety)
- Do not commit secrets into repository.
- If a secret is committed, remove it from history with `git filter-repo` or `git filter-branch`.
- Add secret files to `.gitignore` (e.g. `llm/Qwen/api.env`).
