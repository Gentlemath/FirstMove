# Changelog

All notable changes to this project will be documented in this file.

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