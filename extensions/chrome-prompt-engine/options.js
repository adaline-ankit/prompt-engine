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

const input = document.getElementById("api-base-url");
const inlineToolbarEnabled = document.getElementById("inline-toolbar-enabled");
const includeSurroundingContext = document.getElementById("include-surrounding-context");
const useXmlTags = document.getElementById("use-xml-tags");
const verbosity = document.getElementById("verbosity");
const reasoningDepth = document.getElementById("reasoning-depth");
const structurePreference = document.getElementById("structure-preference");
const groundingMode = document.getElementById("grounding-mode");
const tone = document.getElementById("tone");
const audience = document.getElementById("audience");
const saveButton = document.getElementById("save");
const resetButton = document.getElementById("reset");
const status = document.getElementById("status");

async function load() {
  const settings = await chrome.storage.sync.get(DEFAULT_SETTINGS);
  input.value = settings.apiBaseUrl || DEFAULT_API_BASE_URL;
  inlineToolbarEnabled.checked = Boolean(settings.inlineToolbarEnabled);
  includeSurroundingContext.checked = Boolean(settings.includeSurroundingContext);
  useXmlTags.checked = Boolean(settings.useXmlTags);
  verbosity.value = settings.verbosity || DEFAULT_SETTINGS.verbosity;
  reasoningDepth.value = settings.reasoningDepth || DEFAULT_SETTINGS.reasoningDepth;
  structurePreference.value = settings.structurePreference || DEFAULT_SETTINGS.structurePreference;
  groundingMode.value = settings.groundingMode || DEFAULT_SETTINGS.groundingMode;
  tone.value = settings.tone || DEFAULT_SETTINGS.tone;
  audience.value = settings.audience || DEFAULT_SETTINGS.audience;
}

saveButton.addEventListener("click", async () => {
  await chrome.storage.sync.set({
    apiBaseUrl: input.value.trim() || DEFAULT_API_BASE_URL,
    inlineToolbarEnabled: inlineToolbarEnabled.checked,
    includeSurroundingContext: includeSurroundingContext.checked,
    useXmlTags: useXmlTags.checked,
    verbosity: verbosity.value,
    reasoningDepth: reasoningDepth.value,
    structurePreference: structurePreference.value,
    groundingMode: groundingMode.value,
    tone: tone.value,
    audience: audience.value.trim(),
  });
  status.textContent = "Saved.";
});

resetButton.addEventListener("click", async () => {
  await chrome.storage.sync.set(DEFAULT_SETTINGS);
  await load();
  status.textContent = "Reset to hosted default.";
});

void load();
