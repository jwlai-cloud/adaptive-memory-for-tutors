# Demo deployment

The demo consists of a Vercel-hosted Next.js UI and two scale-to-zero Cloud
Run services: the REST API and the optional MCP endpoint. Cloud Run receives
the Zep and OpenAI credentials from Secret Manager; they are never included in
the image or committed to Git.

## Cloud Run

The project deployment is scripted and pinned to the personal Google Cloud
project `agent-era`. It reads the three required values from the local,
gitignored `.env`, creates new Secret Manager versions, deploys the REST API
from this repository's `Dockerfile`, waits for `/health`, and prints the URL.

```bash
python3 scripts/deploy_cloud_run.py
```

The script activates the `personal` gcloud configuration by default, prints
the active account and project, refuses service-account identities, and asks
for an explicit `deploy` confirmation. Pass `--account your-email@example.com`
to select a specific already-authenticated personal Google account, or `--yes`
only after reviewing the printed account and project.

It deploys with `--min-instances=0`, the three secret environment variables,
and `INSIGHT_MODEL=gpt-5.6-luna`. Deploy the optional MCP endpoint separately
with the same source, overriding its command to
`python -m api.mcp_server.server` and setting `MCP_TRANSPORT=streamable-http`.
Its endpoint is `/mcp`.

The REST service is publicly routable but still requires the demo bearer token.
Set `CORS_ORIGINS` to the final Vercel production URL after deploying the UI.

## Vercel

In `demo-ui`, use `vercel env add` to set these Production variables before
running `vercel --prod`:

| Variable | Value |
| --- | --- |
| `API_BASE_URL` | The HTTPS URL of `adaptive-tutor-api` |
| `BACKEND_API_KEY` | The same low-privilege value as `demo-api-key` |

Both values remain server-side in Vercel. The Next.js proxy attaches the token
to requests to the backend, so it is not placed in browser JavaScript, an
iframe URL, or the host page that embeds the widget.
