# Demo deployment

The demo consists of a Vercel-hosted Next.js UI and two scale-to-zero Cloud
Run services: the REST API and the optional MCP endpoint. Cloud Run receives
the Zep and OpenAI credentials from Secret Manager; they are never included in
the image or committed to Git.

## Cloud Run

From the repository root, set `PROJECT_ID` and `REGION` to your Google Cloud
project and region. Enable Cloud Run, Cloud Build, Artifact Registry, and
Secret Manager, then add the three values from your local `.env` interactively
to Secret Manager as `zep-api-key`, `openai-api-key`, and `demo-api-key`.

Deploy `adaptive-tutor-api` from this repository with the `Dockerfile`,
`--min-instances=0`, the three secret environment variables, and
`INSIGHT_MODEL=gpt-5.6-luna`. Deploy the MCP endpoint with the same source,
overriding its command to `python -m api.mcp_server.server` and setting
`MCP_TRANSPORT=streamable-http`. Its endpoint is `/mcp`.

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
