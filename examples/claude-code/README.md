# Claude Code MCP Setup

Local stdio:

```bash
prompt-engine mcp stdio
```

Hosted or local HTTP:

```bash
prompt-engine mcp http --host 127.0.0.1 --port 8001 --path /mcp
```

Then register Prompt Engine with Claude Code using its MCP configuration flow and point it to either:

- the stdio command `prompt-engine mcp stdio`
- or the Streamable HTTP URL `http://127.0.0.1:8001/mcp`
