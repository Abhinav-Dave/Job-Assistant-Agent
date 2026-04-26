const executeButton = document.getElementById("execute-fill");
const optionsButton = document.getElementById("open-options");
const statusEl = document.getElementById("status");
const telemetryEl = document.getElementById("telemetry");

function setExecuteLoading(loading) {
  executeButton.disabled = loading;
  executeButton.textContent = loading ? "Executing..." : "Execute fill in browser tab";
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#be123c" : "#334155";
}

function setTelemetry(telemetry) {
  if (!telemetry) {
    telemetryEl.textContent = "No telemetry yet.";
    return;
  }
  telemetryEl.textContent = `${telemetry.successfulFills}/${telemetry.mappedFields} fields filled on ${new Date(
    telemetry.completedAt
  ).toLocaleTimeString()}`;
}

async function getActiveTabId() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    throw new Error("No active tab found.");
  }
  return tab.id;
}

async function loadLastTelemetry() {
  const response = await chrome.runtime.sendMessage({ type: "JA_GET_LAST_TELEMETRY" });
  if (response?.ok) {
    setTelemetry(response.telemetry);
  }
}

async function getBridgeContext() {
  const response = await chrome.runtime.sendMessage({ type: "JA_GET_BRIDGE_CONTEXT" });
  return response?.ok ? response.context : null;
}

async function requestContextSyncFromWebApp() {
  const response = await chrome.runtime.sendMessage({ type: "JA_GET_BRIDGE_CONTEXT" });
  const appOrigin = response?.appOrigin || "http://localhost:3000";
  const tabs = await chrome.tabs.query({ url: `${appOrigin}/*` });
  if (!tabs.length) {
    return false;
  }
  const tab = tabs[0];
  if (!tab?.id) {
    return false;
  }
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["content-script.js"],
  });
  await chrome.tabs.sendMessage(tab.id, { type: "JA_REQUEST_CONTEXT_SYNC" });
  await new Promise((resolve) => setTimeout(resolve, 250));
  return true;
}

async function ensureBridgeContext() {
  let context = await getBridgeContext();
  if (context) {
    return context;
  }
  await requestContextSyncFromWebApp();
  context = await getBridgeContext();
  return context;
}

async function executeWithRetry(tabId) {
  try {
    return await chrome.tabs.sendMessage(tabId, { type: "JA_EXECUTE_FILL_IN_TAB" });
  } catch (error) {
    const message = String(error?.message || error);
    if (!message.includes("Receiving end does not exist")) {
      throw error;
    }
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content-script.js"],
    });
    await new Promise((resolve) => setTimeout(resolve, 150));
    return chrome.tabs.sendMessage(tabId, { type: "JA_EXECUTE_FILL_IN_TAB" });
  }
}

executeButton.addEventListener("click", async () => {
  setExecuteLoading(true);
  setStatus("Executing fill in active tab...");
  try {
    const context = await ensureBridgeContext();
    if (!context) {
      throw new Error(
        "Bridge context missing. Open the web app dashboard, keep it logged in, then try again."
      );
    }

    const tabId = await getActiveTabId();
    const response = await executeWithRetry(tabId);
    if (!response?.ok) {
      throw new Error(response?.error || "Fill execution failed.");
    }
    setStatus("Fill execution completed.");
    setTelemetry(response.telemetry);
  } catch (error) {
    setStatus(String(error.message || error), true);
  } finally {
    setExecuteLoading(false);
  }
});

optionsButton.addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

void loadLastTelemetry();
void ensureBridgeContext().then((context) => {
  if (!context) {
    setStatus("Waiting for dashboard context sync.", true);
  }
});
