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
| `NEXT_PUBLIC_API_BASE_URL` | The HTTPS URL of `adaptive-tutor-api` |
| `NEXT_PUBLIC_API_KEY` | The same low-privilege value as `demo-api-key` |

`NEXT_PUBLIC_API_KEY` is delivered to the browser because this demo makes
direct REST calls. It is an access token, not a secret: do not reuse it for
Zep, OpenAI, or any privileged account.
