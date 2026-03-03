# Job Finder

Local web app for AI-assisted job discovery and auto-apply.

## Quick Start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

Open:
- Dashboard: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`

## Internet Search (No Key Required)

```bash
export JOB_PROVIDER=public
```

Optional providers and AI scoring are documented in:
- [backend/README.md](backend/README.md)

## Project Structure

- `backend/` FastAPI app, discovery/adapters, dashboard assets
- `docs/` architecture notes
