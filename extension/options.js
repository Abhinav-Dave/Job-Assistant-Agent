const APP_ORIGIN_KEY = "ja_app_origin";

const appOriginInput = document.getElementById("app-origin");
const saveButton = document.getElementById("save");
const statusEl = document.getElementById("status");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#be123c" : "#334155";
}

async function loadOptions() {
  const values = await chrome.storage.local.get([APP_ORIGIN_KEY]);
  appOriginInput.value = values[APP_ORIGIN_KEY] || "http://localhost:3000";
}

saveButton.addEventListener("click", async () => {
  const appOrigin = appOriginInput.value.trim();
  if (!appOrigin) {
    setStatus("App origin is required.", true);
    return;
  }
  await chrome.storage.local.set({ [APP_ORIGIN_KEY]: appOrigin });
  setStatus("Options saved.");
});

void loadOptions();
