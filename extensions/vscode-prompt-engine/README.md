# Vibe Prompt Engine for VS Code and Cursor

This extension sends selected text or pasted prompts to the hosted Prompt Engine service and returns an optimized prompt, detected intent, applied skills, and a prompt diff.

## Commands

- `Prompt Engine: Open Optimizer`
- `Prompt Engine: Optimize Selection`
- `Prompt Engine: Replace Selection With Optimized Prompt`
- `Prompt Engine: Copy Optimized Prompt`

## Local development

```bash
cd extensions/vscode-prompt-engine
npm install
npm run build
```

Then:

- VS Code: `Extensions: Install from VSIX...` after `npm run package`
- Cursor: use the same `.vsix`, or run the extension in Extension Development Host

## Configuration

- `promptEngine.apiBaseUrl`

Default:

```text
https://prompt-engine-mcp-pewnieev4a-el.a.run.app
```
