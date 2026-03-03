# Job Apply Assistant (Local Web App)

This is a local web app for a single user running on their own computer.

- No sign-in required.
- One built-in local user is used by the dashboard.
- You fill out profile + resume once, then run discovery and auto-apply.

## Run

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

## Internet Search Setup (No Key Required)

Default mode now uses a public internet job feed (no API key):

```bash
export JOB_PROVIDER=public
```

When using the dashboard's Discover flow, you can choose multiple `search_sources` in one run:
- `public` (public feed, no key)
- `linkedin_web`
- `indeed_web`
- `google_web`

Optional: switch to JSearch via RapidAPI for broader source coverage:

```bash
export JOB_PROVIDER=jsearch
export RAPIDAPI_KEY=your_key
export RAPIDAPI_HOST=jsearch.p.rapidapi.com
```

Optional AI scoring:

```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4o-mini
```

Other options:

```bash
export PLAYWRIGHT_HEADLESS=true
export VAULT_FERNET_KEY=your_fernet_key
```

## Main Endpoints

- `POST /users` save/update profile
- `POST /resume` parse and store resume text
- `POST /jobs/discover` discover jobs from configured provider
- `POST /automation/discover-and-auto-apply` discover + AI score + apply
- `POST /automation/auto-apply-specific` apply in bulk to specific job IDs
- `POST /applications/browser-apply` run Playwright adapter (linkedin/indeed/glassdoor)
- `GET /applications` view application states
- `POST /vault/credentials` store encrypted provider credentials metadata locally
- `GET /vault/credentials/{user_id}` list stored credential provider metadata

## Local Dashboard Flow

1. Save profile.
2. Paste resume and parse.
3. Run "Discover + Auto Apply".
   - Supports multiple query tracks, focus fields (IT/Education/Business/etc.), title include/exclude filters, and education filters.
4. If needed, use "Browser Adapter Apply" for specific postings.
5. Monitor statuses in the Applications table and Activity Log.

## Discover + Auto Apply Parameters

- `query`: primary search phrase
- `search_sources`: comma-separated sources to search (`public, linkedin_web, indeed_web, google_web`)
- `additional_queries`: extra search phrases (comma-separated in dashboard)
- `focus_fields`: domain targeting like `IT`, `Education`, `Business`, `Healthcare`, `Finance`
- `include_titles`: only keep jobs whose title includes these keywords
- `exclude_titles`: remove jobs whose title includes these keywords
- `education_levels`: filter by education requirement keywords (`high school`, `associate`, `bachelor`, `master`, `doctorate`)

## Compliance Note

Use official APIs/partner programs and respect platform terms. If a flow needs captcha or manual input,
the system should pause and request user action.
