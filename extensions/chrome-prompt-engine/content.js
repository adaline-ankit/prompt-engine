const DEFAULT_API_BASE_URL = "https://prompt-engine-mcp-pewnieev4a-el.a.run.app";
const DEFAULT_SETTINGS = {
  apiBaseUrl: DEFAULT_API_BASE_URL,
  inlineToolbarEnabled: true,
  includeSurroundingContext: true,
  useXmlTags: true,
  verbosity: "balanced",
  reasoningDepth: "standard",
  structurePreference: "auto",
  groundingMode: "strict",
  tone: "professional",
  audience: "",
};

const CHAT_EDITOR_SELECTORS = [
  "#prompt-textarea",
  "textarea[data-id]",
  "textarea",
  "div[role='textbox'][contenteditable='true']",
  "div[contenteditable='true'][data-lexical-editor='true']",
  "[contenteditable='true']",
];

let lastFocusedElement = null;
let toolbarRoot = null;
let optimizeButton = null;
let settingsButton = null;
let settingsPanel = null;
let statusChip = null;
let observer = null;
let activeRequest = null;
let cachedSettings = { ...DEFAULT_SETTINGS };

function isChatLikeHost() {
  return /chatgpt\.com$|chat\.openai\.com$|claude\.ai$|gemini\.google\.com$|copilot\.microsoft\.com$/.test(
    window.location.hostname
  );
}

function isEditable(element) {
  if (!element || !(element instanceof Element)) {
    return false;
  }
  if (toolbarRoot?.contains(element)) {
    return false;
  }
  if (element instanceof HTMLTextAreaElement) {
    return !element.readOnly && !element.disabled;
  }
  if (element instanceof HTMLInputElement) {
    return ["text", "search", "url", "email"].includes(element.type) && !element.readOnly && !element.disabled;
  }
  return element.isContentEditable === true;
}

function focusedEditable() {
  if (isEditable(lastFocusedElement)) {
    return lastFocusedElement;
  }
  if (isEditable(document.activeElement)) {
    return document.activeElement;
  }
  return findPreferredEditor();
}

function findPreferredEditor() {
  for (const selector of CHAT_EDITOR_SELECTORS) {
    const element = document.querySelector(selector);
    if (isEditable(element)) {
      return element;
    }
  }
  return null;
}

function findAnchor(element) {
  if (!element) {
    return null;
  }
  return (
    element.closest("form") ||
    element.closest("[data-testid*='composer']") ||
    element.closest("[data-testid*='input']") ||
    element.closest("[class*='composer']") ||
    element.closest("[class*='input']") ||
    element.parentElement
  );
}

function ensureToolbar() {
  if (toolbarRoot) {
    return;
  }

  toolbarRoot = document.createElement("div");
  toolbarRoot.id = "vibe-prompt-engine-toolbar";
  Object.assign(toolbarRoot.style, {
    position: "fixed",
    top: "0",
    left: "0",
    zIndex: "2147483647",
    display: "none",
    minWidth: "220px",
    padding: "10px",
    borderRadius: "16px",
    background: "rgba(15, 23, 42, 0.92)",
    color: "#f8fafc",
    boxShadow: "0 20px 40px rgba(15, 23, 42, 0.24)",
    backdropFilter: "blur(12px)",
    fontFamily: 'Inter, "Segoe UI", sans-serif',
  });

  const row = document.createElement("div");
  Object.assign(row.style, {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  });

  optimizeButton = document.createElement("button");
  optimizeButton.type = "button";
  optimizeButton.textContent = "Optimize";
  Object.assign(optimizeButton.style, {
    border: "0",
    borderRadius: "999px",
    padding: "9px 14px",
    background: "linear-gradient(135deg, #0f766e, #14b8a6)",
    color: "#ffffff",
    fontWeight: "700",
    fontSize: "12px",
    cursor: "pointer",
  });

  settingsButton = document.createElement("button");
  settingsButton.type = "button";
  settingsButton.textContent = "Tune";
  Object.assign(settingsButton.style, {
    border: "1px solid rgba(148, 163, 184, 0.35)",
    borderRadius: "999px",
    padding: "9px 12px",
    background: "rgba(255, 255, 255, 0.08)",
    color: "#f8fafc",
    fontWeight: "600",
    fontSize: "12px",
    cursor: "pointer",
  });

  statusChip = document.createElement("div");
  Object.assign(statusChip.style, {
    display: "none",
    marginTop: "8px",
    fontSize: "11px",
    lineHeight: "1.3",
    color: "#cbd5e1",
  });

  settingsPanel = document.createElement("div");
  Object.assign(settingsPanel.style, {
    display: "none",
    marginTop: "10px",
    paddingTop: "10px",
    borderTop: "1px solid rgba(148, 163, 184, 0.2)",
    gap: "8px",
  });

  optimizeButton.addEventListener("click", () => {
    void optimizeFocusedPrompt();
  });
  settingsButton.addEventListener("click", () => {
    settingsPanel.style.display = settingsPanel.style.display === "grid" ? "none" : "grid";
  });
  toolbarRoot.addEventListener("mousedown", (event) => {
    event.preventDefault();
  });

  row.appendChild(optimizeButton);
  row.appendChild(settingsButton);
  toolbarRoot.appendChild(row);
  toolbarRoot.appendChild(statusChip);
  toolbarRoot.appendChild(settingsPanel);
  document.documentElement.appendChild(toolbarRoot);
  renderSettingsPanel();
}

function createField(labelText, inputElement) {
  const wrapper = document.createElement("label");
  Object.assign(wrapper.style, {
    display: "grid",
    gap: "4px",
    fontSize: "11px",
    color: "#cbd5e1",
  });
  const label = document.createElement("span");
  label.textContent = labelText;
  wrapper.appendChild(label);
  wrapper.appendChild(inputElement);
  return wrapper;
}

function createSelect(options, value, onChange) {
  const select = document.createElement("select");
  Object.assign(select.style, inputStyles());
  for (const option of options) {
    const item = document.createElement("option");
    item.value = option.value;
    item.textContent = option.label;
    select.appendChild(item);
  }
  select.value = value;
  select.addEventListener("change", () => onChange(select.value));
  return select;
}

function createTextInput(value, placeholder, onChange) {
  const input = document.createElement("input");
  input.type = "text";
  input.value = value;
  input.placeholder = placeholder;
  Object.assign(input.style, inputStyles());
  input.addEventListener("change", () => onChange(input.value.trim()));
  return input;
}

function createCheckbox(labelText, checked, onChange) {
  const wrapper = document.createElement("label");
  Object.assign(wrapper.style, {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "11px",
    color: "#cbd5e1",
  });
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = checked;
  input.addEventListener("change", () => onChange(input.checked));
  const label = document.createElement("span");
  label.textContent = labelText;
  wrapper.appendChild(input);
  wrapper.appendChild(label);
  return wrapper;
}

function inputStyles() {
  return {
    width: "100%",
    padding: "8px 10px",
    borderRadius: "10px",
    border: "1px solid rgba(148, 163, 184, 0.35)",
    background: "rgba(255, 255, 255, 0.08)",
    color: "#f8fafc",
    fontSize: "12px",
    boxSizing: "border-box",
  };
}

function renderSettingsPanel() {
  ensureToolbar();
  settingsPanel.innerHTML = "";
  Object.assign(settingsPanel.style, {
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    display: settingsPanel.style.display === "grid" ? "grid" : "none",
  });

  const fields = [
    createField(
      "Verbosity",
      createSelect(
        [
          { value: "concise", label: "Concise" },
          { value: "balanced", label: "Balanced" },
          { value: "elaborate", label: "Elaborate" },
        ],
        cachedSettings.verbosity,
        (value) => saveSetting("verbosity", value)
      )
    ),
    createField(
      "Reasoning",
      createSelect(
        [
          { value: "light", label: "Light" },
          { value: "standard", label: "Standard" },
          { value: "deep", label: "Deep" },
        ],
        cachedSettings.reasoningDepth,
        (value) => saveSetting("reasoningDepth", value)
      )
    ),
    createField(
      "Structure",
      createSelect(
        [
          { value: "auto", label: "Auto" },
          { value: "sections", label: "Sections" },
          { value: "bullets", label: "Bullets" },
          { value: "json", label: "JSON" },
        ],
        cachedSettings.structurePreference,
        (value) => saveSetting("structurePreference", value)
      )
    ),
    createField(
      "Tone",
      createSelect(
        [
          { value: "professional", label: "Professional" },
          { value: "direct", label: "Direct" },
          { value: "technical", label: "Technical" },
          { value: "friendly", label: "Friendly" },
        ],
        cachedSettings.tone,
        (value) => saveSetting("tone", value)
      )
    ),
    createField(
      "Audience",
      createTextInput(cachedSettings.audience, "developers, execs, support", (value) => saveSetting("audience", value))
    ),
    createField(
      "Grounding",
      createSelect(
        [
          { value: "strict", label: "Strict" },
          { value: "balanced", label: "Balanced" },
        ],
        cachedSettings.groundingMode,
        (value) => saveSetting("groundingMode", value)
      )
    ),
    createCheckbox("Use surrounding page context", cachedSettings.includeSurroundingContext, (value) =>
      saveSetting("includeSurroundingContext", value)
    ),
    createCheckbox("Use XML-style sections", cachedSettings.useXmlTags, (value) => saveSetting("useXmlTags", value)),
  ];

  for (const field of fields) {
    settingsPanel.appendChild(field);
  }
}

async function saveSetting(key, value) {
  cachedSettings[key] = value;
  await chrome.storage.sync.set({ [key]: value });
  setStatus("Saved settings.", "success", 1000);
}

function setStatus(message, kind = "neutral", timeoutMs = 0) {
  ensureToolbar();
  if (!statusChip) {
    return;
  }
  statusChip.textContent = message;
  statusChip.style.display = message ? "block" : "none";
  statusChip.style.color =
    kind === "error" ? "#fecaca" : kind === "success" ? "#99f6e4" : "#cbd5e1";
  if (timeoutMs > 0) {
    window.setTimeout(() => {
      if (statusChip.textContent === message) {
        statusChip.textContent = "";
        statusChip.style.display = "none";
      }
    }, timeoutMs);
  }
}

async function loadSettings() {
  cachedSettings = await chrome.storage.sync.get(DEFAULT_SETTINGS);
  renderSettingsPanel();
}

function getSelectionTextFromEditable(element) {
  if (!element) {
    return "";
  }

  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
    const start = element.selectionStart ?? 0;
    const end = element.selectionEnd ?? 0;
    return end > start ? element.value.slice(start, end) : element.value;
  }

  if (element.isContentEditable) {
    const selection = window.getSelection();
    const selectedText = selection ? selection.toString() : "";
    return selectedText || "";
  }

  return "";
}

function getEditableValue(element) {
  if (!element) {
    return "";
  }
  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
    return element.value || "";
  }
  if (element.isContentEditable) {
    return element.innerText || "";
  }
  return "";
}

function getSurroundingContext(element) {
  if (!cachedSettings.includeSurroundingContext) {
    return "";
  }
  if (!element) {
    return document.body?.innerText?.trim().slice(0, 2500) || "";
  }
  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
    return element.value.trim().slice(0, 2500);
  }
  if (element.isContentEditable) {
    const container =
      element.closest("main, article, form, section, [role='main'], [data-testid*='conversation'], [data-testid*='chat']") ||
      element;
    return (container.innerText || "").trim().slice(0, 3000);
  }
  return document.body?.innerText?.trim().slice(0, 2500) || "";
}

function buildPromptContext(element, selectedText) {
  const context = {
    page_title: document.title || "",
    page_url: window.location.href || "",
    window_title: document.title || "",
    verbosity: cachedSettings.verbosity,
    reasoning_depth: cachedSettings.reasoningDepth,
    structure_preference: cachedSettings.structurePreference,
    grounding_mode: cachedSettings.groundingMode,
    use_xml_tags: cachedSettings.useXmlTags,
    tone: cachedSettings.tone,
  };

  if (cachedSettings.audience) {
    context.audience = cachedSettings.audience;
  }
  if (selectedText) {
    context.selected_text = selectedText;
  }
  if (cachedSettings.includeSurroundingContext) {
    context.surrounding_text = getSurroundingContext(element);
  }
  return context;
}

async function getStoredEndpoint() {
  const payload = await chrome.storage.sync.get(DEFAULT_SETTINGS);
  cachedSettings = { ...DEFAULT_SETTINGS, ...payload };
  return String(cachedSettings.apiBaseUrl || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function replaceTextInEditable(element, text) {
  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
    const start = element.selectionStart ?? 0;
    const end = element.selectionEnd ?? start;
    const value = element.value;
    if (end > start) {
      element.value = value.slice(0, start) + text + value.slice(end);
      const caret = start + text.length;
      element.selectionStart = caret;
      element.selectionEnd = caret;
    } else {
      element.value = text;
    }
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  if (element?.isContentEditable) {
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0 && selection.toString()) {
      const range = selection.getRangeAt(0);
      range.deleteContents();
      range.insertNode(document.createTextNode(text));
      selection.removeAllRanges();
      return true;
    }

    element.focus();
    document.execCommand("selectAll", false, null);
    document.execCommand("insertText", false, text);
    element.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertText" }));
    return true;
  }

  return false;
}

async function optimizeFocusedPrompt() {
  const editable = focusedEditable();
  if (!editable || activeRequest) {
    return;
  }

  const selectedText = getSelectionTextFromEditable(editable).trim();
  const prompt = selectedText || getEditableValue(editable).trim();
  if (!prompt) {
    setStatus("No prompt text found.", "error", 1800);
    return;
  }

  optimizeButton.disabled = true;
  optimizeButton.textContent = "Optimizing...";
  activeRequest = Promise.resolve();
  setStatus("Optimizing prompt…");

  try {
    const apiBaseUrl = await getStoredEndpoint();
    const response = await fetch(`${apiBaseUrl}/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        context: buildPromptContext(editable, selectedText || prompt),
      }),
    });

    if (!response.ok) {
      throw new Error(`Prompt Engine request failed: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    if (!replaceTextInEditable(editable, result.final_prompt || "")) {
      throw new Error("Could not replace the active prompt.");
    }
    setStatus(`Optimized for ${result.intent || "general"} intent.`, "success", 1600);
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Prompt optimization failed.", "error", 2600);
  } finally {
    activeRequest = null;
    optimizeButton.disabled = false;
    optimizeButton.textContent = "Optimize";
    positionToolbar();
  }
}

function positionToolbar() {
  ensureToolbar();
  const editor = focusedEditable();
  if (!toolbarRoot || !editor || !cachedSettings.inlineToolbarEnabled) {
    hideToolbar();
    return;
  }

  const rect = editor.getBoundingClientRect();
  if (rect.width < 120 || rect.bottom < 0 || rect.top > window.innerHeight) {
    hideToolbar();
    return;
  }

  const anchor = findAnchor(editor);
  const anchorRect = anchor?.getBoundingClientRect?.() || rect;
  const top = Math.max(12, anchorRect.top - 62);
  const left = Math.min(window.innerWidth - 240, Math.max(12, anchorRect.right - 236));

  toolbarRoot.style.display = "block";
  toolbarRoot.style.top = `${top}px`;
  toolbarRoot.style.left = `${left}px`;
}

function hideToolbar() {
  ensureToolbar();
  toolbarRoot.style.display = "none";
}

function handlePotentialEditor(element) {
  if (isEditable(element)) {
    lastFocusedElement = element;
    positionToolbar();
  } else if (isChatLikeHost()) {
    lastFocusedElement = findPreferredEditor();
    positionToolbar();
  }
}

function installObserver() {
  if (observer) {
    return;
  }

  observer = new MutationObserver(() => {
    if (isChatLikeHost()) {
      lastFocusedElement = focusedEditable();
      positionToolbar();
    }
  });
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["class", "style", "contenteditable"],
  });
}

document.addEventListener("focusin", (event) => {
  handlePotentialEditor(event.target);
});

document.addEventListener("click", (event) => {
  if (toolbarRoot?.contains(event.target)) {
    return;
  }
  handlePotentialEditor(event.target);
});

document.addEventListener("selectionchange", () => {
  if (document.activeElement) {
    handlePotentialEditor(document.activeElement);
  }
});

document.addEventListener(
  "scroll",
  () => {
    positionToolbar();
  },
  true
);

window.addEventListener("resize", () => {
  positionToolbar();
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "PROMPT_ENGINE_GET_SELECTION") {
    const editable = focusedEditable();
    const text = editable ? getSelectionTextFromEditable(editable) || getEditableValue(editable) : window.getSelection()?.toString() || "";
    sendResponse({
      text,
      context: buildPromptContext(editable, text),
    });
    return true;
  }

  if (message.type === "PROMPT_ENGINE_REPLACE_SELECTION") {
    const editable = focusedEditable();
    const replaced = editable ? replaceTextInEditable(editable, message.text || "") : false;
    sendResponse({ replaced });
    return true;
  }

  if (message.type === "PROMPT_ENGINE_OPTIMIZE_ACTIVE") {
    void optimizeFocusedPrompt().then(() => sendResponse({ ok: true }));
    return true;
  }

  return false;
});

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "sync") {
    return;
  }
  for (const [key, value] of Object.entries(changes)) {
    cachedSettings[key] = value.newValue;
  }
  renderSettingsPanel();
  positionToolbar();
});

void loadSettings().then(() => {
  ensureToolbar();
  installObserver();
  lastFocusedElement = focusedEditable();
  if (lastFocusedElement || isChatLikeHost()) {
    positionToolbar();
  }
});
