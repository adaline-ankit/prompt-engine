import * as crypto from "node:crypto";
import * as vscode from "vscode";

interface TransformationStep {
  name: string;
  description: string;
}

interface OptimizeResponse {
  final_prompt: string;
  intent: string;
  skills_applied: string[];
  prompt_diff: string;
  transformations: TransformationStep[];
}

class PromptEnginePanel {
  private static currentPanel: PromptEnginePanel | undefined;

  static show(
    extensionUri: vscode.Uri,
    initialPrompt: string,
    onMessage: (message: any, panel: PromptEnginePanel) => void
  ): PromptEnginePanel {
    if (PromptEnginePanel.currentPanel) {
      PromptEnginePanel.currentPanel.panel.reveal(vscode.ViewColumn.Beside);
      PromptEnginePanel.currentPanel.setInitialPrompt(initialPrompt);
      return PromptEnginePanel.currentPanel;
    }

    const panel = vscode.window.createWebviewPanel(
      "promptEngineOptimizer",
      "Prompt Engine Optimizer",
      vscode.ViewColumn.Beside,
      { enableScripts: true }
    );

    PromptEnginePanel.currentPanel = new PromptEnginePanel(panel, extensionUri, initialPrompt, onMessage);
    return PromptEnginePanel.currentPanel;
  }

  private readonly panel: vscode.WebviewPanel;
  private readonly extensionUri: vscode.Uri;

  private constructor(
    panel: vscode.WebviewPanel,
    extensionUri: vscode.Uri,
    initialPrompt: string,
    onMessage: (message: any, panel: PromptEnginePanel) => void
  ) {
    this.panel = panel;
    this.extensionUri = extensionUri;
    this.panel.webview.html = this.getHtml(initialPrompt);
    this.panel.webview.onDidReceiveMessage((message) => onMessage(message, this));
    this.panel.onDidDispose(() => {
      PromptEnginePanel.currentPanel = undefined;
    });
  }

  setInitialPrompt(prompt: string): void {
    if (!prompt) {
      return;
    }
    this.panel.webview.postMessage({ type: "setPrompt", prompt });
  }

  updateResult(result: OptimizeResponse): void {
    this.panel.webview.postMessage({ type: "setResult", result });
  }

  showError(message: string): void {
    this.panel.webview.postMessage({ type: "setError", message });
  }

  private getHtml(initialPrompt: string): string {
    const nonce = crypto.randomUUID().replace(/-/g, "");
    const promptJson = JSON.stringify(initialPrompt);

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Prompt Engine</title>
  <style>
    :root {
      color-scheme: light dark;
      --border: rgba(127, 127, 127, 0.35);
      --surface: rgba(127, 127, 127, 0.08);
      --accent: #0f766e;
      --accent-strong: #115e59;
      --error: #b91c1c;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      padding: 18px;
      display: grid;
      gap: 14px;
      background: var(--surface);
    }
    h1 {
      margin: 0;
      font-size: 18px;
    }
    textarea, pre {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      background: rgba(255, 255, 255, 0.78);
      color: inherit;
    }
    textarea {
      min-height: 180px;
      resize: vertical;
      font: inherit;
    }
    pre {
      min-height: 120px;
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }
    .row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 10px 14px;
      cursor: pointer;
      font: inherit;
      background: var(--accent);
      color: white;
    }
    button.secondary {
      background: rgba(127, 127, 127, 0.18);
      color: inherit;
    }
    button:disabled {
      opacity: 0.6;
      cursor: default;
    }
    .chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .chip {
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 4px 10px;
      background: rgba(255, 255, 255, 0.7);
      font-size: 12px;
    }
    .meta {
      display: grid;
      gap: 8px;
    }
    .error {
      color: var(--error);
      font-weight: 600;
    }
    .label {
      font-size: 12px;
      opacity: 0.75;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
  </style>
</head>
<body>
  <h1>Prompt Engine Optimizer</h1>
  <div>
    <div class="label">Original Prompt</div>
    <textarea id="prompt" placeholder="Paste a prompt here and optimize it before sending."></textarea>
  </div>
  <div class="row">
    <button id="optimize">Optimize Prompt</button>
    <button id="copy" class="secondary" disabled>Copy Optimized</button>
    <button id="replace" class="secondary" disabled>Replace Active Selection</button>
  </div>
  <div id="error" class="error"></div>
  <div class="meta">
    <div>
      <div class="label">Intent</div>
      <div id="intent">Unknown</div>
    </div>
    <div>
      <div class="label">Skills Applied</div>
      <div id="skills" class="chips"></div>
    </div>
    <div>
      <div class="label">Optimized Prompt</div>
      <pre id="optimized">Optimize a prompt to see the result.</pre>
    </div>
    <div>
      <div class="label">Prompt Diff</div>
      <pre id="diff">No diff yet.</pre>
    </div>
  </div>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const promptEl = document.getElementById("prompt");
    const optimizeButton = document.getElementById("optimize");
    const copyButton = document.getElementById("copy");
    const replaceButton = document.getElementById("replace");
    const optimizedEl = document.getElementById("optimized");
    const diffEl = document.getElementById("diff");
    const intentEl = document.getElementById("intent");
    const skillsEl = document.getElementById("skills");
    const errorEl = document.getElementById("error");
    let latestOptimized = "";

    promptEl.value = ${promptJson};

    optimizeButton.addEventListener("click", () => {
      errorEl.textContent = "";
      optimizeButton.disabled = true;
      vscode.postMessage({ type: "optimize", prompt: promptEl.value });
    });

    copyButton.addEventListener("click", () => {
      vscode.postMessage({ type: "copy", text: latestOptimized });
    });

    replaceButton.addEventListener("click", () => {
      vscode.postMessage({ type: "replace", text: latestOptimized });
    });

    window.addEventListener("message", (event) => {
      const message = event.data;
      if (message.type === "setPrompt") {
        promptEl.value = message.prompt;
        return;
      }

      if (message.type === "setError") {
        optimizeButton.disabled = false;
        errorEl.textContent = message.message;
        return;
      }

      if (message.type === "setResult") {
        optimizeButton.disabled = false;
        latestOptimized = message.result.final_prompt;
        optimizedEl.textContent = message.result.final_prompt;
        diffEl.textContent = message.result.prompt_diff || "No diff returned.";
        intentEl.textContent = message.result.intent;
        skillsEl.innerHTML = "";
        for (const skill of message.result.skills_applied || []) {
          const chip = document.createElement("div");
          chip.className = "chip";
          chip.textContent = skill;
          skillsEl.appendChild(chip);
        }
        copyButton.disabled = !latestOptimized;
        replaceButton.disabled = !latestOptimized;
      }
    });
  </script>
</body>
</html>`;
  }
}

function apiBaseUrl(): string {
  return vscode.workspace.getConfiguration().get<string>(
    "promptEngine.apiBaseUrl",
    "https://prompt-engine-mcp-pewnieev4a-el.a.run.app"
  );
}

async function optimizePrompt(prompt: string): Promise<OptimizeResponse> {
  return optimizePromptWithContext(prompt, {});
}

async function optimizePromptWithContext(
  prompt: string,
  context: Record<string, unknown>
): Promise<OptimizeResponse> {
  const trimmed = prompt.trim();
  if (!trimmed) {
    throw new Error("Prompt is empty.");
  }

  const response = await fetch(`${apiBaseUrl().replace(/\/$/, "")}/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: trimmed, context })
  });

  if (!response.ok) {
    throw new Error(`Prompt Engine request failed: ${response.status} ${response.statusText}`);
  }

  return (await response.json()) as OptimizeResponse;
}

function selectionOrDocument(editor: vscode.TextEditor | undefined): { text: string; range: vscode.Range | null } {
  if (!editor) {
    return { text: "", range: null };
  }

  if (!editor.selection.isEmpty) {
    return { text: editor.document.getText(editor.selection), range: editor.selection };
  }

  return { text: editor.document.getText(), range: null };
}

function buildEditorContext(editor: vscode.TextEditor | undefined, selectedText: string): Record<string, unknown> {
  if (!editor) {
    return {};
  }

  const { document, selection } = editor;
  const context: Record<string, unknown> = {
    editor_language: document.languageId,
    file_path: document.uri.scheme === "file" ? document.uri.fsPath : document.uri.toString()
  };
  const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);

  if (workspaceFolder) {
    context.workspace_context = `Workspace: ${workspaceFolder.name}`;
  }

  if (!selection.isEmpty) {
    const startLine = Math.max(0, selection.start.line - 8);
    const endLine = Math.min(document.lineCount - 1, selection.end.line + 8);
    const surroundingRange = new vscode.Range(
      new vscode.Position(startLine, 0),
      document.lineAt(endLine).range.end
    );
    const surroundingText = document.getText(surroundingRange).trim();
    context.selected_text = selectedText;
    if (surroundingText && surroundingText !== selectedText.trim()) {
      context.surrounding_text = surroundingText;
    }
  }

  return context;
}

async function replaceInEditor(text: string): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    throw new Error("No active editor is available.");
  }

  const targetRange = editor.selection.isEmpty
    ? new vscode.Range(editor.document.positionAt(0), editor.document.positionAt(editor.document.getText().length))
    : editor.selection;

  await editor.edit((builder) => builder.replace(targetRange, text));
}

export function activate(context: vscode.ExtensionContext): void {
  const handlePanelMessage = async (message: any, panel: PromptEnginePanel) => {
    try {
      if (message.type === "optimize") {
        panel.updateResult(
          await optimizePromptWithContext(
            message.prompt,
            buildEditorContext(vscode.window.activeTextEditor, String(message.prompt || ""))
          )
        );
        return;
      }
      if (message.type === "copy") {
        await vscode.env.clipboard.writeText(message.text ?? "");
        void vscode.window.showInformationMessage("Optimized prompt copied.");
        return;
      }
      if (message.type === "replace") {
        await replaceInEditor(message.text ?? "");
        void vscode.window.showInformationMessage("Editor content replaced with optimized prompt.");
      }
    } catch (error) {
      panel.showError(error instanceof Error ? error.message : "Prompt optimization failed.");
    }
  };

  const openPanel = vscode.commands.registerCommand("promptEngine.openOptimizer", async () => {
    const editor = vscode.window.activeTextEditor;
    const { text } = selectionOrDocument(editor);
    PromptEnginePanel.show(context.extensionUri, text, handlePanelMessage);
  });

  const optimizeSelection = vscode.commands.registerCommand("promptEngine.optimizeSelection", async () => {
    try {
      const { text } = selectionOrDocument(vscode.window.activeTextEditor);
      const panel = PromptEnginePanel.show(context.extensionUri, text, handlePanelMessage);
      panel.updateResult(await optimizePromptWithContext(text, buildEditorContext(vscode.window.activeTextEditor, text)));
    } catch (error) {
      void vscode.window.showErrorMessage(error instanceof Error ? error.message : "Prompt optimization failed.");
    }
  });

  const replaceSelection = vscode.commands.registerCommand("promptEngine.replaceSelection", async () => {
    try {
      const editor = vscode.window.activeTextEditor;
      const { text } = selectionOrDocument(editor);
      const result = await optimizePromptWithContext(text, buildEditorContext(editor, text));
      await replaceInEditor(result.final_prompt);
      void vscode.window.showInformationMessage("Selection replaced with optimized prompt.");
    } catch (error) {
      void vscode.window.showErrorMessage(error instanceof Error ? error.message : "Prompt optimization failed.");
    }
  });

  const copyOptimized = vscode.commands.registerCommand("promptEngine.copyOptimizedPrompt", async () => {
    try {
      const editor = vscode.window.activeTextEditor;
      const { text } = selectionOrDocument(editor);
      const result = await optimizePromptWithContext(text, buildEditorContext(editor, text));
      await vscode.env.clipboard.writeText(result.final_prompt);
      void vscode.window.showInformationMessage("Optimized prompt copied to clipboard.");
    } catch (error) {
      void vscode.window.showErrorMessage(error instanceof Error ? error.message : "Prompt optimization failed.");
    }
  });

  context.subscriptions.push(openPanel, optimizeSelection, replaceSelection, copyOptimized);
}

export function deactivate(): void {}
