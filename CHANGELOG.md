# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial pipeline wiring for LLM workspace generation.
- Backend environment variable loading from `backend/.env`.
- LLM fallback to rule-based generation when llm call fails.
- `dev.sh` script for local development with backend and frontend startup.

### Fixed
- Fixed `.env` load order so `LLM_MODEL` and `LLM_ENDPOINT_URL` are available when services initialize.
- Added robust JSON response parsing for LLM responses (handles singleton object and list output).

### Security
- Remove `llm/Qwen/api.env` from Git tracking and add to `.gitignore`.

## [0.1.0] - 2026-04-01

### Added
- Base implementation for task generation via LLM and rule fallback.
- REST API endpoint `/workspace/generate`.
- LLM configuration via `backend/.env`.

### Fixed
- Dependency & venv setup instructions in `README.md`.
