# Demo UI

Next.js demo for the Adaptive Memory for Tutors infrastructure. It consumes the
authenticated REST API; it never talks to Zep directly.

## Run locally

Start the API from the repository root (the `API_KEY` must match the UI key):

```bash
uvicorn api.rest.app:app --reload
```

Then configure and run the UI:

```bash
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_KEY to the API_KEY from the repository .env file.
npm install
npm run dev
```

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000` and can point
at a deployed API for the demo.

## Demo pages

- `/compare` — stateless mock response beside the live persisted insight.
- `/timeline` — live kana event history, checkpoint chart, and insight audit feed.
- `/heatmap` — live states across the Japanese kana and chemistry notation case studies.

The browser-visible key is intentionally only a minimal hackathon-demo token;
replace it with a proper session/auth mechanism before production use.
