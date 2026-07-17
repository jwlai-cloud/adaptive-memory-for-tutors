# Demo UI

Next.js demo for the Adaptive Memory for Tutors infrastructure. It consumes the
authenticated REST API; it never talks to Zep directly.

## Run locally

Start the API from the repository root:

```bash
uvicorn api.rest.app:app --reload
```

Then configure and run the UI:

```bash
cp .env.local.example .env.local
# Set API_BASE_URL and BACKEND_API_KEY (matching the repository API_KEY).
npm install
npm run dev
```

`API_BASE_URL` defaults to `http://localhost:8000` and can point at a deployed
API; `BACKEND_API_KEY` remains server-only in the Next.js proxy.

## Demo pages

- `/compare` — stateless mock response beside the live persisted insight.
- `/timeline` — live kana event history, checkpoint chart, and insight audit feed.
- `/heatmap` — live states across the Japanese kana and chemistry notation case studies.

The browser-visible key is intentionally only a minimal hackathon-demo token;
replace it with a proper session/auth mechanism before production use.
