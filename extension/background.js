const BRIDGE_CONTEXT_KEY = "ja_bridge_context";
const APP_ORIGIN_KEY = "ja_app_origin";
const LAST_TELEMETRY_KEY = "ja_last_telemetry";
const LAST_APPLICATION_EVENT_KEY = "ja_last_application_event";
const MAPPING_CACHE_TTL_MS = 2 * 60 * 1000;
const mappingCache = new Map();

async function getFromStorage(keys) {
  return chrome.storage.local.get(keys);
}

async function setInStorage(values) {
  await chrome.storage.local.set(values);
}

async function getBridgeContext() {
  return chrome.storage.session.get([BRIDGE_CONTEXT_KEY]);
}

async function setBridgeContext(context) {
  await chrome.storage.session.set({ [BRIDGE_CONTEXT_KEY]: context });
}

async function broadcastTelemetry(payload) {
  const tabs = await chrome.tabs.query({});
  await Promise.allSettled(
    tabs
      .filter((tab) => typeof tab.id === "number")
      .map((tab) =>
        chrome.tabs.sendMessage(tab.id, {
          type: "JA_EXTENSION_TELEMETRY",
          payload,
        })
      )
  );
}

async function broadcastApplicationEvent(payload) {
  const tabs = await chrome.tabs.query({});
  await Promise.allSettled(
    tabs
      .filter((tab) => typeof tab.id === "number")
      .map((tab) =>
        chrome.tabs.sendMessage(tab.id, {
          type: "JA_EXTENSION_APPLICATION_EVENT",
          payload,
        })
      )
  );
}

async function requestAutofillMappingFromBackend(payload) {
  const contextStorage = await getBridgeContext();
  const context = contextStorage[BRIDGE_CONTEXT_KEY];
  if (!context?.apiBaseUrl || !context?.accessToken) {
    return { ok: false, error: "Bridge context missing API base URL or access token." };
  }
  const pageUrl = payload?.pageUrl || "";
  const profileVersion = context.profile?.updated_at || context.syncedAt || "";
  const cacheKey = `${pageUrl}|${profileVersion}`;
  const cached = mappingCache.get(cacheKey);
  if (cached && Date.now() - cached.createdAt < MAPPING_CACHE_TTL_MS) {
    return { ok: true, data: cached.data, cached: true };
  }

  const response = await fetch(`${context.apiBaseUrl}/api/autofill`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${context.accessToken}`,
    },
    body: JSON.stringify({
      page_url: pageUrl,
      ...(context.profile ? { profile: context.profile } : {}),
    }),
  });

  if (!response.ok) {
    let message = `Autofill request failed (${response.status})`;
    try {
      const json = await response.json();
      message = json?.message || json?.error || message;
    } catch {
      // Ignore JSON parse errors and keep fallback message.
    }
    return { ok: false, error: message };
  }

  const data = await response.json();
  mappingCache.set(cacheKey, {
    data,
    createdAt: Date.now(),
  });
  return { ok: true, data };
}

function samePageCandidate(tabUrl, targetPageUrl) {
  try {
    const tabParsed = new URL(tabUrl);
    const targetParsed = new URL(targetPageUrl);
    return (
      tabParsed.hostname === targetParsed.hostname &&
      (tabParsed.pathname === targetParsed.pathname ||
        tabParsed.href.startsWith(targetParsed.href) ||
        targetParsed.href.startsWith(tabParsed.href))
    );
  } catch {
    return false;
  }
}

async function executeFillWithRetry(tabId) {
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

async function executeFillForPage(pageUrl) {
  const allTabs = await chrome.tabs.query({});
  let targetTab = allTabs.find((tab) => tab.url && samePageCandidate(tab.url, pageUrl));
  if (!targetTab?.id) {
    targetTab = await chrome.tabs.create({ url: pageUrl, active: true });
    if (!targetTab?.id) {
      return {
        ok: false,
        error: "Unable to open ATS tab for this job URL.",
      };
    }
    await new Promise((resolve) => setTimeout(resolve, 1200));
  } else {
    await chrome.tabs.update(targetTab.id, { active: true });
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  return executeFillWithRetry(targetTab.id);
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message?.type) {
    sendResponse({ ok: false, error: "Invalid message." });
    return false;
  }

  if (message.type === "JA_STORE_BRIDGE_CONTEXT") {
    const origin =
      message.payload?.appOrigin ||
      (sender.url ? new URL(sender.url).origin : "http://localhost:3000");
    Promise.all([
      setBridgeContext(message.payload?.context ?? null),
      setInStorage({ [APP_ORIGIN_KEY]: origin }),
    ])
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  if (message.type === "JA_GET_BRIDGE_CONTEXT") {
    Promise.all([getBridgeContext(), getFromStorage([APP_ORIGIN_KEY])])
      .then(([sessionStorage, localStorage]) =>
        sendResponse({
          ok: true,
          context: sessionStorage[BRIDGE_CONTEXT_KEY] ?? null,
          appOrigin: localStorage[APP_ORIGIN_KEY] ?? "http://localhost:3000",
        })
      )
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  if (message.type === "JA_TELEMETRY_REPORT") {
    const payload = message.payload ?? null;
    setInStorage({ [LAST_TELEMETRY_KEY]: payload })
      .then(async () => {
        if (payload) {
          await broadcastTelemetry(payload);
        }
        sendResponse({ ok: true });
      })
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  if (message.type === "JA_GET_LAST_TELEMETRY") {
    getFromStorage([LAST_TELEMETRY_KEY])
      .then((storage) =>
        sendResponse({
          ok: true,
          telemetry: storage[LAST_TELEMETRY_KEY] ?? null,
        })
      )
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  if (message.type === "JA_APPLICATION_EVENT_REPORT") {
    const payload = message.payload ?? null;
    setInStorage({ [LAST_APPLICATION_EVENT_KEY]: payload })
      .then(async () => {
        if (payload) {
          await broadcastApplicationEvent(payload);
        }
        sendResponse({ ok: true });
      })
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  if (message.type === "JA_REQUEST_AUTOFILL_MAPPING") {
    requestAutofillMappingFromBackend(message.payload)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  if (message.type === "JA_EXECUTE_FILL_FOR_PAGE") {
    executeFillForPage(message.payload?.pageUrl || "")
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: String(error) }));
    return true;
  }

  sendResponse({ ok: false, error: `Unsupported message type: ${message.type}` });
  return false;
});
