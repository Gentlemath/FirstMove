# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.1] - 2026-04-02
### Added
- optimizate the LLM so that generated tasks are more articulated
- Structured tool shortcuts for task cards so the frontend can render clickable tool chips.
- Controlled backend tool registry for canonical web-based shortcuts.
- Focused backend tests for task normalization, LLM response repair, and tool alias handling.

### Changed
- Refactored workspace task generation so prompt building, response parsing, fallback heuristics, and tool resolution live in smaller functional units.
- Strengthened the workspace-generation prompt with clearer output rules and examples for higher-quality task cards.
- Updated the frontend task detail panel to render structured tool shortcuts as links instead of plain text labels.

### Fixed
- Task normalization now incorporates freeform `raw_task_text` instead of ignoring it.
- LLM response handling now validates task count and ordering, repairs invalid JSON once, and falls back more reliably when output is unusable.
- Generic or vague `first_step` and `hint` text is now replaced with more concrete fallback guidance.



## [0.1.0] - 2026-04-01
### Added
- Version control for both the backend and frontend.
- GitHub CI workflow in `ci.yml`.
- Initial pipeline wiring for LLM workspace generation.
- Backend environment variable loading from `backend/.env`.
- Rule-based fallback when the LLM call fails.
- `dev.sh` for local development with backend and frontend startup.

### Fixed
- Import ordering so all imports appear before function definitions.
- `.env` load order so `LLM_MODEL` and `LLM_ENDPOINT_URL` are available during service initialization.
- JSON response parsing for LLM responses to handle both singleton object and list outputs.
- Robustness of `test_environment.py` for external test environments.

### Security
- Removed `llm/Qwen/api.env` from Git tracking and added it to `.gitignore`.