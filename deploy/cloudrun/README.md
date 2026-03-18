# Cloud Run Deployment

Prompt Engine can be deployed as a hosted Streamable HTTP MCP endpoint on Cloud Run.

Recommended public endpoint:

```text
https://api.your-domain.com/mcp
```

## One-time setup

1. Create a GCP project
2. Enable:
   - Cloud Run
   - Artifact Registry
   - Secret Manager
3. Choose one GitHub Actions authentication mode:
   - recommended: GitHub OIDC Workload Identity Federation
   - fallback: service account JSON key
4. Add GitHub repository secrets:
   - for OIDC:
     - `GCP_WORKLOAD_IDENTITY_PROVIDER`
     - `GCP_SERVICE_ACCOUNT`
   - or for JSON key auth:
     - `GCP_CREDENTIALS_JSON`
5. Add GitHub repository variables:
   - `GCP_PROJECT_ID`
   - `GCP_REGION`
   - `CLOUD_RUN_SERVICE`

The GitHub workflow deploys from source. Cloud Run builds the container and stores the runtime image in Artifact Registry during deployment.

## Required GitHub configuration

Repository secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`: full provider resource name, for example `projects/123456789/locations/global/workloadIdentityPools/github/providers/github`
- `GCP_SERVICE_ACCOUNT`: deployer service account email, for example `github-deployer@your-project.iam.gserviceaccount.com`
- `GCP_CREDENTIALS_JSON`: optional fallback JSON key. Use this only if you are not using workload identity federation.

Repository variables:

- `GCP_PROJECT_ID`: your Google Cloud project id
- `GCP_REGION`: for example `us-central1`
- `CLOUD_RUN_SERVICE`: for example `prompt-engine`

The workflow now validates these values before it tries to authenticate, so failures should be explicit.

## Runtime configuration

Set environment variables and secrets in Cloud Run:

- `PROMPT_ENGINE_CONFIG=config/config.yaml`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`

## Local equivalent

```bash
docker build -t prompt-engine .
docker run -p 8000:8000 prompt-engine
```

Then expose:

```text
http://localhost:8000/mcp
```

## After the first deploy

The workflow summary prints:

- Cloud Run service URL
- MCP endpoint URL at `/mcp`

Use that hosted MCP endpoint in Cursor or Claude Code once the deploy succeeds.
