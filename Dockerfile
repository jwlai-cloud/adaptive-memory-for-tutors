FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY engine ./engine
COPY seed-data ./seed-data

EXPOSE 8080

# Cloud Run supplies PORT at runtime. This default serves the REST API; the
# MCP service overrides the command and sets MCP_TRANSPORT=streamable-http.
CMD ["sh", "-c", "uvicorn api.rest.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
