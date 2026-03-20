const DEFAULT_API_BASE_URL = "https://prompt-engine-mcp-pewnieev4a-el.a.run.app";

const input = document.getElementById("api-base-url");
const saveButton = document.getElementById("save");
const resetButton = document.getElementById("reset");
const status = document.getElementById("status");

async function load() {
  const { apiBaseUrl } = await chrome.storage.sync.get({ apiBaseUrl: DEFAULT_API_BASE_URL });
  input.value = apiBaseUrl || DEFAULT_API_BASE_URL;
}

saveButton.addEventListener("click", async () => {
  const value = input.value.trim() || DEFAULT_API_BASE_URL;
  await chrome.storage.sync.set({ apiBaseUrl: value });
  status.textContent = "Saved.";
});

resetButton.addEventListener("click", async () => {
  input.value = DEFAULT_API_BASE_URL;
  await chrome.storage.sync.set({ apiBaseUrl: DEFAULT_API_BASE_URL });
  status.textContent = "Reset to hosted default.";
});

void load();
