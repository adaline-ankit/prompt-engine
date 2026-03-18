# Public Release Plan

Prompt Engine should be released in two forms:

1. Installable package for local `stdio` MCP usage in Cursor and Claude Code
2. Hosted Streamable HTTP MCP server for team and SaaS usage

## Distribution channels

### 1. PyPI

Publish the Python package so users can run:

```bash
uvx prompt-engine mcp stdio
```

or:

```bash
pipx install prompt-engine
prompt-engine mcp stdio
```

### 2. GitHub Releases

Create a GitHub release for every tag:

- source tarball
- wheel
- release notes
- example Cursor config snippets

### 3. GHCR container image

Publish a container image on every tagged release:

```text
ghcr.io/<org>/prompt-engine:<version>
ghcr.io/<org>/prompt-engine:latest
```

This image is the basis for Cloud Run, Railway, Fly.io, ECS, or Kubernetes.

### 4. Hosted MCP endpoint

Primary production endpoint:

```text
https://api.<your-domain>/mcp
```

Users in Cursor or Claude Code then add a hosted MCP server instead of running local code.

## Recommended production stack

For the first public hosted deployment:

- Build and push container to GHCR
- Deploy to Google Cloud Run from source so Google builds and stores the runtime image in Artifact Registry
- Put custom domain and TLS in front of it
- Store provider API keys in Cloud Run secrets

Cloud Run is a good first production target because it is container-native, autoscaling, HTTPS-ready, and simple to operate for an HTTP MCP service.

## First release checklist

1. Create a GitHub repository for the project
2. Configure PyPI Trusted Publishing for the repo
3. Set GitHub Actions variables:
   - `GCP_REGION`
   - `CLOUD_RUN_SERVICE`
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`
4. Enable GitHub Packages permissions for GHCR publishing
5. Tag a release:

```bash
git tag v0.1.0
git push origin main --tags
```

For this repository, the canonical source is:

- GitHub: [adaline-ankit/prompt-engine](https://github.com/adaline-ankit/prompt-engine)
- PyPI project: [prompt-engine](https://pypi.org/project/prompt-engine/)

`VERSION` is the release source of truth. Keep `VERSION` and `pyproject.toml` aligned. You can either:

```bash
python scripts/release_bump.py --release-type patch
```

or run the GitHub Actions `release-bump` workflow, which updates `VERSION`, `pyproject.toml`, `CHANGELOG.md`, creates a tag, and pushes it.

## How users should install it

### Cursor local

```json
{
  "mcpServers": {
    "prompt-engine": {
      "command": "uvx",
      "args": ["prompt-engine", "mcp", "stdio"]
    }
  }
}
```

If PyPI is not live yet, bootstrap from GitHub instead:

```json
{
  "mcpServers": {
    "prompt-engine": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/adaline-ankit/prompt-engine",
        "prompt-engine",
        "mcp",
        "stdio"
      ]
    }
  }
}
```

### Cursor hosted

```json
{
  "mcpServers": {
    "prompt-engine": {
      "url": "https://api.<your-domain>/mcp"
    }
  }
}
```

## Discovery

After the hosted endpoint is stable, submit the server to the community-driven MCP Registry:

- [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry)
