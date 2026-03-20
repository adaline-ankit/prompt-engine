let lastFocusedElement = null;

function isEditable(element) {
  if (!element) {
    return false;
  }
  if (element instanceof HTMLTextAreaElement) {
    return true;
  }
  if (element instanceof HTMLInputElement) {
    return ["text", "search", "url", "email"].includes(element.type);
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
  }
});

document.addEventListener("mouseup", () => {
  if (isEditable(document.activeElement)) {
    lastFocusedElement = document.activeElement;
  }
});

document.addEventListener("keyup", () => {
  if (isEditable(document.activeElement)) {
    lastFocusedElement = document.activeElement;
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "PROMPT_ENGINE_GET_SELECTION") {
    const editable = focusedEditable();
    const text = editable
      ? getSelectionTextFromEditable(editable)
      : (window.getSelection()?.toString() || "");
    sendResponse({ text });
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
