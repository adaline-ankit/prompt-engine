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

const promptEl = document.getElementById("prompt");
const optimizedEl = document.getElementById("optimized");
const diffEl = document.getElementById("diff");
const intentEl = document.getElementById("intent");
const skillsEl = document.getElementById("skills");
const statusEl = document.getElementById("status");
const optimizeButton = document.getElementById("optimize");
const importButton = document.getElementById("import-selection");
const replaceButton = document.getElementById("replace-selection");
const copyButton = document.getElementById("copy-optimized");
const settingsButton = document.getElementById("open-options");

let latestOptimized = "";
let latestContext = {};

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#b91c1c" : "";
}

async function getStoredEndpoint() {
  const settings = await chrome.storage.sync.get(DEFAULT_SETTINGS);
  latestContext = buildSettingsContext(settings, latestContext);
  return String(settings.apiBaseUrl || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function buildSettingsContext(settings, existingContext) {
  return {
    ...existingContext,
    verbosity: settings.verbosity,
    reasoning_depth: settings.reasoningDepth,
    structure_preference: settings.structurePreference,
    grounding_mode: settings.groundingMode,
    use_xml_tags: settings.useXmlTags,
    tone: settings.tone,
    ...(settings.audience ? { audience: settings.audience } : {})
  };
}

async function sendToActiveTab(message) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("No active tab found.");
  }
  return chrome.tabs.sendMessage(tab.id, message);
}

function renderSkills(skills) {
  skillsEl.innerHTML = "";
  for (const skill of skills || []) {
    const chip = document.createElement("div");
    chip.className = "chip";
    chip.textContent = skill;
    skillsEl.appendChild(chip);
  }
}

async function optimizePrompt() {
  const prompt = promptEl.value.trim();
  if (!prompt) {
    setStatus("Prompt is empty.", true);
    return;
  }

  setStatus("Optimizing...");
  optimizeButton.disabled = true;

  try {
    const apiBaseUrl = await getStoredEndpoint();
    const response = await fetch(`${apiBaseUrl}/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, context: latestContext })
    });

    if (!response.ok) {
      throw new Error(`Prompt Engine request failed: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    latestOptimized = result.final_prompt || "";
    optimizedEl.value = latestOptimized;
    diffEl.textContent = result.prompt_diff || "No diff returned.";
    intentEl.textContent = result.intent || "unknown";
    renderSkills(result.skills_applied);
    replaceButton.disabled = !latestOptimized;
    copyButton.disabled = !latestOptimized;
    setStatus("Prompt optimized.");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Prompt optimization failed.", true);
  } finally {
    optimizeButton.disabled = false;
  }
}

importButton.addEventListener("click", async () => {
  try {
    const payload = await sendToActiveTab({ type: "PROMPT_ENGINE_GET_SELECTION" });
    promptEl.value = payload?.text || "";
    latestContext = payload?.context || {};
    setStatus(promptEl.value ? "Imported selection." : "No selection or editable text found.", !promptEl.value);
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Could not access the active tab.", true);
  }
});

optimizeButton.addEventListener("click", () => {
  void optimizePrompt();
});

replaceButton.addEventListener("click", async () => {
  if (!latestOptimized) {
    return;
  }
  try {
    await sendToActiveTab({ type: "PROMPT_ENGINE_REPLACE_SELECTION", text: latestOptimized });
    setStatus("Page selection replaced.");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Could not replace page selection.", true);
  }
});

copyButton.addEventListener("click", async () => {
  if (!latestOptimized) {
    return;
  }
  await navigator.clipboard.writeText(latestOptimized);
  setStatus("Optimized prompt copied.");
});

settingsButton.addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});
