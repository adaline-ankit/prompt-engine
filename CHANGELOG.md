# Changelog

## 0.1.4

- Fix PyPI release artifact upload so only Python distributions are published
- Keep extension artifacts on GitHub releases without polluting the PyPI publish job

## 0.1.3

- Add a page-injected `Optimize` button beside active browser prompt fields for one-click in-place rewriting
- Improve prompt refinement with stronger language normalization, request reframing, and structured context blocks
- Expand eval coverage for shorthand prompts and context-aware summaries

## 0.1.2

- Add first-party VS Code and Cursor extension for prompt optimization
- Add first-party Chrome extension for browser prompt optimization and page selection replacement
- Include extension packaging in CI and tagged GitHub releases

## 0.1.1

- Align PyPI distribution name with the published project: `vibe-prompt-engine`
- Add `vibe-prompt-engine` CLI aliases for `uvx` and `pipx` installs
- Update release automation and docs for the renamed PyPI package

## 0.1.0

- Initial public release of Prompt Engine
- Prompt optimization core, skill system, CLI, API, eval harness
- MCP server for Cursor, Claude Code, and other compatible clients
- `stdio` and Streamable HTTP transports
- Cursor config helpers and example configs
