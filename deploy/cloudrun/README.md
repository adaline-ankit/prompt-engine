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
3. Configure GitHub OIDC workload identity for deployment
4. Add GitHub repository secrets:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`
5. Add GitHub repository variables:
   - `GCP_REGION`
   - `CLOUD_RUN_SERVICE`

The GitHub workflow deploys from source. Cloud Run builds the container and stores the runtime image in Artifact Registry during deployment.

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
