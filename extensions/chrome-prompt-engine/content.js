const DEFAULT_API_BASE_URL = "https://prompt-engine-mcp-pewnieev4a-el.a.run.app";

let lastFocusedElement = null;
let overlayRoot = null;
let optimizeButton = null;
let statusChip = null;
let activeRequest = null;

function ensureOverlay() {
  if (overlayRoot) {
    return;
  }

  overlayRoot = document.createElement("div");
  overlayRoot.id = "vibe-prompt-engine-inline-root";
  overlayRoot.style.position = "fixed";
  overlayRoot.style.top = "0";
  overlayRoot.style.left = "0";
  overlayRoot.style.zIndex = "2147483647";
  overlayRoot.style.display = "none";
  overlayRoot.style.pointerEvents = "auto";
  overlayRoot.style.fontFamily = 'Inter, "Segoe UI", sans-serif';

  optimizeButton = document.createElement("button");
  optimizeButton.type = "button";
  optimizeButton.textContent = "Optimize";
  optimizeButton.style.border = "0";
  optimizeButton.style.borderRadius = "999px";
  optimizeButton.style.padding = "8px 12px";
  optimizeButton.style.background = "#0f766e";
  optimizeButton.style.color = "#ffffff";
  optimizeButton.style.fontSize = "12px";
  optimizeButton.style.fontWeight = "700";
  optimizeButton.style.boxShadow = "0 10px 25px rgba(15, 118, 110, 0.24)";
  optimizeButton.style.cursor = "pointer";

  statusChip = document.createElement("div");
  statusChip.style.marginTop = "6px";
  statusChip.style.padding = "4px 10px";
  statusChip.style.borderRadius = "999px";
  statusChip.style.background = "rgba(15, 23, 42, 0.9)";
  statusChip.style.color = "#ffffff";
  statusChip.style.fontSize = "11px";
  statusChip.style.lineHeight = "1.2";
  statusChip.style.display = "none";
  statusChip.style.width = "fit-content";
  statusChip.textContent = "";

  optimizeButton.addEventListener("click", () => {
    void optimizeFocusedPrompt();
  });

  overlayRoot.addEventListener("mousedown", (event) => {
    event.preventDefault();
  });

  overlayRoot.appendChild(optimizeButton);
  overlayRoot.appendChild(statusChip);
  document.documentElement.appendChild(overlayRoot);
}

function setOverlayState(message, kind = "idle") {
  ensureOverlay();
  if (!statusChip || !optimizeButton) {
    return;
  }

  if (!message) {
    statusChip.style.display = "none";
    statusChip.textContent = "";
  } else {
    statusChip.style.display = "block";
    statusChip.textContent = message;
  }

  optimizeButton.disabled = kind === "loading";
  optimizeButton.style.opacity = kind === "loading" ? "0.7" : "1";
  optimizeButton.textContent = kind === "loading" ? "Optimizing..." : "Optimize";

  if (kind === "error") {
    statusChip.style.background = "rgba(185, 28, 28, 0.92)";
  } else if (kind === "success") {
    statusChip.style.background = "rgba(15, 118, 110, 0.92)";
  } else {
    statusChip.style.background = "rgba(15, 23, 42, 0.9)";
  }
}

function isEditable(element) {
  if (!element) {
    return false;
  }
  if (!(element instanceof Element)) {
    return false;
  }
  if (element.closest("#vibe-prompt-engine-inline-root")) {
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
  return null;
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
    return selectedText || element.innerText || "";
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
  if (!element) {
    return document.body?.innerText?.trim().slice(0, 2500) || "";
  }

  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
    return element.value.trim().slice(0, 2500);
  }

  if (element.isContentEditable) {
    const container = element.closest("main, article, form, [role='main'], [data-testid*='conversation'], [data-testid*='chat']") || element;
    return (container.innerText || "").trim().slice(0, 2500);
  }

  return document.body?.innerText?.trim().slice(0, 2500) || "";
}

function elementAnchorRect(element) {
  const rect = element?.getBoundingClientRect?.();
  if (!rect) {
    return null;
  }
  if (rect.width < 80 || rect.height < 28) {
    return null;
  }
  if (rect.bottom < 0 || rect.top > window.innerHeight) {
    return null;
  }
  return rect;
}

function positionOverlay() {
  ensureOverlay();
  const editable = focusedEditable();
  const rect = editable ? elementAnchorRect(editable) : null;
  if (!rect || !overlayRoot) {
    hideOverlay();
    return;
  }

  const top = Math.min(window.innerHeight - 56, Math.max(12, rect.top + 8));
  const left = Math.min(window.innerWidth - 120, Math.max(12, rect.right - 104));

  overlayRoot.style.display = "block";
  overlayRoot.style.top = `${top}px`;
  overlayRoot.style.left = `${left}px`;
}

function hideOverlay() {
  ensureOverlay();
  if (!overlayRoot) {
    return;
  }
  overlayRoot.style.display = "none";
  setOverlayState("");
}

async function getStoredEndpoint() {
  const payload = await chrome.storage.sync.get({ apiBaseUrl: DEFAULT_API_BASE_URL });
  return String(payload.apiBaseUrl || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function buildPromptContext(element, selectedText) {
  return {
    selected_text: selectedText,
    surrounding_text: getSurroundingContext(element),
    page_title: document.title || "",
    page_url: window.location.href || "",
    window_title: document.title || ""
  };
}

async function optimizeFocusedPrompt() {
  const editable = focusedEditable();
  if (!editable || activeRequest) {
    return;
  }

  const selectedText = getSelectionTextFromEditable(editable).trim();
  const baseText = selectedText || getEditableValue(editable).trim();
  if (!baseText) {
    setOverlayState("No prompt text found.", "error");
    window.setTimeout(() => setOverlayState(""), 1600);
    return;
  }

  activeRequest = Promise.resolve();
  setOverlayState("Optimizing prompt", "loading");

  try {
    const apiBaseUrl = await getStoredEndpoint();
    const response = await fetch(`${apiBaseUrl}/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: baseText,
        context: buildPromptContext(editable, selectedText || baseText)
      })
    });

    if (!response.ok) {
      throw new Error(`Prompt Engine request failed: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    const replaced = replaceTextInEditable(editable, result.final_prompt || "");
    if (!replaced) {
      throw new Error("Could not replace the active prompt.");
    }

    setOverlayState("Optimized in place", "success");
    window.setTimeout(() => setOverlayState(""), 1400);
    positionOverlay();
  } catch (error) {
    setOverlayState(error instanceof Error ? error.message : "Prompt optimization failed.", "error");
    window.setTimeout(() => setOverlayState(""), 2200);
  } finally {
    activeRequest = null;
  }
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
    if (selection && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      range.deleteContents();
      range.insertNode(document.createTextNode(text));
      selection.removeAllRanges();
      return true;
    }
    element.innerText = text;
    return true;
  }

  return false;
}

document.addEventListener("focusin", (event) => {
  if (isEditable(event.target)) {
    lastFocusedElement = event.target;
    positionOverlay();
  }
});

document.addEventListener("mouseup", () => {
  if (isEditable(document.activeElement)) {
    lastFocusedElement = document.activeElement;
    positionOverlay();
  }
});

document.addEventListener("keyup", () => {
  if (isEditable(document.activeElement)) {
    lastFocusedElement = document.activeElement;
    positionOverlay();
  }
});

document.addEventListener("scroll", () => {
  positionOverlay();
}, true);

window.addEventListener("resize", () => {
  positionOverlay();
});

document.addEventListener("click", (event) => {
  if (!isEditable(event.target)) {
    hideOverlay();
  }
});

document.addEventListener("selectionchange", () => {
  positionOverlay();
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "PROMPT_ENGINE_GET_SELECTION") {
    const editable = focusedEditable();
    const text = editable
      ? getSelectionTextFromEditable(editable)
      : (window.getSelection()?.toString() || "");
    sendResponse({
      text,
      context: {
        ...buildPromptContext(editable, text),
      }
    });
    return true;
  }

  if (message.type === "PROMPT_ENGINE_REPLACE_SELECTION") {
    const editable = focusedEditable();
    const replaced = editable
      ? replaceTextInEditable(editable, message.text || "")
      : false;
    sendResponse({ replaced });
    return true;
  }

  return false;
});
