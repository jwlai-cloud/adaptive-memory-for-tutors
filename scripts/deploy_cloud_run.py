#!/usr/bin/env python3
"""Deploy the REST API to the personal ``agent-era`` Google Cloud project.

Secrets are read locally from .env and sent directly to Secret Manager. They
are never printed, written to source control, or baked into the container.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional

PROJECT_ID = "agent-era"
DEFAULT_REGION = "australia-southeast1"
SERVICE_NAME = "adaptive-tutor-api"
VERCEL_ORIGIN = "https://adaptive-memory-for-tutors.vercel.app"
SECRETS = {
    "zep-api-key": "ZEP_API_KEY",
    "openai-api-key": "OPENAI_API_KEY",
    "demo-api-key": "API_KEY",
}


def run(*args: str, input_text: Optional[str] = None, capture: bool = False) -> str:
    """Run gcloud without echoing secret input or credentials."""
    result = subprocess.run(
        list(args),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        check=True,
    )
    return result.stdout.strip() if capture else ""


def read_dotenv(path: Path) -> dict[str, str]:
    """Read the simple KEY=value format used by this project's .env file."""
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def ensure_secret(name: str, value: str) -> None:
    """Create a secret if needed, then add a new current version."""
    exists = subprocess.run(
        ["gcloud", "secrets", "describe", name, "--project", PROJECT_ID],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    if not exists:
        run(
            "gcloud",
            "secrets",
            "create",
            name,
            "--project",
            PROJECT_ID,
            "--replication-policy=automatic",
        )
    run(
        "gcloud",
        "secrets",
        "versions",
        "add",
        name,
        "--project",
        PROJECT_ID,
        "--data-file=-",
        input_text=value,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--configuration", default="personal")
    parser.add_argument(
        "--account",
        help="Personal Google account to activate; must already be authenticated in gcloud.",
    )
    parser.add_argument("--yes", action="store_true", help="Skip the account/project confirmation.")
    args = parser.parse_args()

    if shutil.which("gcloud") is None:
        raise SystemExit("gcloud is not installed. Install Google Cloud CLI, then run gcloud auth login.")

    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / ".env"
    if not env_path.is_file():
        raise SystemExit("Missing .env. Copy .env.example and configure the three required keys first.")
    env_values = read_dotenv(env_path)
    missing = [env_key for env_key in SECRETS.values() if not env_values.get(env_key)]
    if missing:
        raise SystemExit(f"Missing required .env values: {', '.join(missing)}")

    run("gcloud", "config", "configurations", "activate", args.configuration)
    if args.account:
        run("gcloud", "config", "set", "account", args.account)
    active_account = run(
        "gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)", capture=True
    )
    if not active_account:
        raise SystemExit("No active Google account. Run gcloud auth login, then retry.")
    if active_account.endswith(".gserviceaccount.com"):
        raise SystemExit("Refusing to deploy with a service account; use your personal Google login instead.")

    print(f"Google account: {active_account}")
    print(f"Google project: {PROJECT_ID}")
    print(f"Region: {args.region}")
    if not args.yes:
        confirmation = input("Type 'deploy' to upload secrets and deploy Cloud Run: ").strip()
        if confirmation != "deploy":
            raise SystemExit("Deployment cancelled.")

    run("gcloud", "config", "set", "project", PROJECT_ID)
    run(
        "gcloud",
        "services",
        "enable",
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "artifactregistry.googleapis.com",
        "secretmanager.googleapis.com",
        "--project",
        PROJECT_ID,
    )

    for secret_name, env_name in SECRETS.items():
        ensure_secret(secret_name, env_values[env_name])

    project_number = run(
        "gcloud",
        "projects",
        "describe",
        PROJECT_ID,
        "--format=value(projectNumber)",
        capture=True,
    )
    runtime_account = f"{project_number}-compute@developer.gserviceaccount.com"
    for secret_name in SECRETS:
        run(
            "gcloud",
            "secrets",
            "add-iam-policy-binding",
            secret_name,
            "--project",
            PROJECT_ID,
            "--member",
            f"serviceAccount:{runtime_account}",
            "--role=roles/secretmanager.secretAccessor",
        )

    run(
        "gcloud",
        "run",
        "deploy",
        SERVICE_NAME,
        "--source",
        str(repo_root),
        "--project",
        PROJECT_ID,
        "--region",
        args.region,
        "--allow-unauthenticated",
        "--port=8080",
        "--min-instances=0",
        "--max-instances=2",
        "--memory=512Mi",
        "--set-env-vars",
        f"INSIGHT_MODEL=gpt-5.6-luna,DEFAULT_TENANT_ID=demo-school,CORS_ORIGINS={VERCEL_ORIGIN}",
        "--set-secrets",
        "ZEP_API_KEY=zep-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,API_KEY=demo-api-key:latest",
    )
    service_url = run(
        "gcloud",
        "run",
        "services",
        "describe",
        SERVICE_NAME,
        "--project",
        PROJECT_ID,
        "--region",
        args.region,
        "--format=value(status.url)",
        capture=True,
    )
    with urllib.request.urlopen(f"{service_url}/health", timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Health check returned HTTP {response.status}")

    print(f"\nCloud Run REST API is live: {service_url}")
    print("\nNext, set these Vercel Production variables and redeploy:")
    print(f"  API_BASE_URL={service_url}")
    print("  BACKEND_API_KEY=<the API_KEY already stored in your local .env>")


if __name__ == "__main__":
    main()
