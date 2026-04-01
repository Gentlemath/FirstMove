# Backend

Suggested stack:
- FastAPI
- SQLite first
- Google Calendar integration
- LLM workspace generation

Suggested endpoints:
- GET /calendar/today
- POST /workspace/generate
- POST /workspace/update
- POST /workspace/summary

Current scaffold:
- `GET /health`
- `GET /calendar/today`
- `POST /workspace/generate`

Current behavior:
- `GET /calendar/today` returns Google Calendar events if the Google token env vars are set
- otherwise it falls back to demo fixed blocks so the frontend can still run
- `POST /workspace/generate` currently uses rule-based task generation, not a real LLM yet

Google Calendar env vars:
- `GOOGLE_CALENDAR_ID`
- `GOOGLE_CALENDAR_TOKEN_PATH`
- `GOOGLE_CALENDAR_TIMEZONE` default: `America/Los_Angeles`

Env file:
- copy `backend/.env.example` to `backend/.env`
- fill in the real values there
- the backend loads `backend/.env` automatically on startup

Generate the Google token file:
1. Download your Google OAuth desktop-app credentials JSON to `backend/credentials.json`
2. Run:
```bash
cd backend
python3 generate_token.py
```
3. A browser will open for Google sign-in and consent
4. The script writes `backend/token.json`
5. Set `GOOGLE_CALENDAR_TOKEN_PATH` in `backend/.env` to that file path

Example requests:
```bash
curl http://127.0.0.1:8000/calendar/today
```

```bash
curl -X POST http://127.0.0.1:8000/workspace/generate \
  -H "Content-Type: application/json" \
  -d '{
    "raw_task_text": "Reply to recruiter\nFinish product spec\nPrepare for project review"
  }'
```
