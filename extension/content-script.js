/** @typedef {import("../frontend/types/extension-bridge").BridgeContextPayload} BridgeContextPayload */
/** @typedef {import("../frontend/types/extension-bridge").ExtensionFillTelemetry} ExtensionFillTelemetry */

const BRIDGE_WEB_SOURCE = "job-assistant-web";
const BRIDGE_EXTENSION_SOURCE = "job-assistant-extension";

function getFieldLabel(element) {
  if (!element) {
    return "";
  }
  if (element.labels?.length) {
    return element.labels[0].innerText?.trim() ?? "";
  }
  const aria = element.getAttribute("aria-label");
  if (aria) {
    return aria.trim();
  }
  return element.name || element.id || element.placeholder || "field";
}

function getFillableElements() {
  return Array.from(document.querySelectorAll("input, textarea, select")).filter((element) => {
    const input = /** @type {HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement} */ (element);
    if (input instanceof HTMLInputElement && input.type === "hidden") {
      return false;
    }
    return !input.disabled && !input.readOnly;
  });
}

function setNativeInputValue(element, value) {
  const prototype =
    element instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
  const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");
  if (descriptor?.set) {
    descriptor.set.call(element, value);
  } else {
    element.value = value;
  }
}

function setElementValue(element, value) {
  if (element instanceof HTMLSelectElement) {
    const exact = Array.from(element.options).find((option) => option.value === value);
    const byLabel = Array.from(element.options).find(
      (option) => option.textContent?.trim().toLowerCase() === value.trim().toLowerCase()
    );
    const chosen = exact || byLabel;
    if (chosen) {
      element.value = chosen.value;
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
      element.dispatchEvent(new Event("blur", { bubbles: true }));
      return true;
    }
    return false;
  }
  element.focus();
  setNativeInputValue(element, value);
  element.dispatchEvent(new InputEvent("input", { bubbles: true, data: value }));
  element.dispatchEvent(new Event("change", { bubbles: true }));
  element.dispatchEvent(new Event("blur", { bubbles: true }));
  return true;
}

function getElementDescriptor(element) {
  return [
    getFieldLabel(element),
    element.id || "",
    element.name || "",
    element.getAttribute("placeholder") || "",
    element.getAttribute("autocomplete") || "",
    element.getAttribute("aria-label") || "",
  ]
    .join(" ")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function includesAny(text, terms) {
  return terms.some((term) => text.includes(term));
}

function isCompatibleFieldType(element, mappingFieldType, profileKey) {
  const descriptor = getElementDescriptor(element);
  const normalizedProfileKey = String(profileKey || "").toLowerCase();
  if (!mappingFieldType) {
    // Still apply profile-key guardrails even if backend type is absent.
    if (normalizedProfileKey === "email") {
      return includesAny(descriptor, ["email", "e-mail", "mail"]) && !includesAny(descriptor, ["address"]);
    }
    if (normalizedProfileKey === "phone") {
      return includesAny(descriptor, ["phone", "mobile", "cell", "tel", "country code", "extension"]);
    }
    if (normalizedProfileKey === "postal_code") {
      return includesAny(descriptor, ["postal", "zip", "pin"]);
    }
    return true;
  }
  const normalizedMappingType = String(mappingFieldType).toLowerCase();
  if (element instanceof HTMLSelectElement) {
    return normalizedMappingType === "select" || normalizedMappingType === "dropdown";
  }
  if (element instanceof HTMLTextAreaElement) {
    return normalizedMappingType === "textarea" || normalizedMappingType === "text";
  }
  if (element instanceof HTMLInputElement) {
    const inputType = (element.type || "text").toLowerCase();
    if (normalizedMappingType === "email" || normalizedProfileKey === "email") {
      const emailishType = inputType === "email" || inputType === "text" || inputType === "search";
      return (
        emailishType &&
        includesAny(descriptor, ["email", "e-mail", "mail"]) &&
        !includesAny(descriptor, ["address line", "street", "city", "postal", "zip", "phone", "mobile"])
      );
    }
    if (normalizedMappingType === "tel" || normalizedProfileKey === "phone") {
      const phoneishType = inputType === "tel" || inputType === "text";
      return (
        phoneishType &&
        includesAny(descriptor, ["phone", "mobile", "cell", "tel", "country code", "extension"]) &&
        !includesAny(descriptor, ["email", "address", "city", "postal", "zip"])
      );
    }
    if (normalizedProfileKey === "address_line1") {
      return (
        ["text", "search"].includes(inputType) &&
        includesAny(descriptor, ["address", "street", "line 1"]) &&
        !includesAny(descriptor, ["email", "phone", "mobile", "city", "postal", "zip", "country"])
      );
    }
    if (normalizedProfileKey === "address_line2") {
      return (
        ["text", "search"].includes(inputType) &&
        includesAny(descriptor, ["address line 2", "line 2", "apt", "suite", "unit", "apartment"])
      );
    }
    if (normalizedProfileKey === "city") {
      return ["text", "search"].includes(inputType) && includesAny(descriptor, ["city", "town"]);
    }
    if (normalizedProfileKey === "province") {
      return ["text", "search"].includes(inputType) && includesAny(descriptor, ["state", "province", "region"]);
    }
    if (normalizedProfileKey === "country") {
      return ["text", "search"].includes(inputType) && includesAny(descriptor, ["country"]);
    }
    if (normalizedProfileKey === "postal_code") {
      return (
        ["text", "search"].includes(inputType) &&
        includesAny(descriptor, ["postal", "zip", "zip code", "postcode", "pin"])
      );
    }
    if (normalizedMappingType === "text") {
      return ["text", "search"].includes(inputType);
    }
  }
  return true;
}

function findBestElement(fieldId, fieldLabel, profileKey, fieldType) {
  const candidates = getFillableElements();
  const loweredId = (fieldId || "").toLowerCase();
  const loweredLabel = (fieldLabel || "").toLowerCase();
  const compatibleCandidates = candidates.filter((element) =>
    isCompatibleFieldType(element, fieldType, profileKey)
  );

  if (loweredId) {
    const idExact = compatibleCandidates.find(
      (element) => (element.id || "").toLowerCase() === loweredId
    );
    if (idExact) {
      return idExact;
    }
    const nameExact = compatibleCandidates.find(
      (element) => (element.name || "").toLowerCase() === loweredId
    );
    if (nameExact) {
      return nameExact;
    }
  }

  if (loweredLabel) {
    const labelExact = compatibleCandidates.find(
      (element) => getFieldLabel(element).trim().toLowerCase() === loweredLabel
    );
    if (labelExact) {
      return labelExact;
    }
  }

  const scored = compatibleCandidates
    .map((element) => {
      const descriptor = getElementDescriptor(element);
      let score = 0;
      if (loweredId && descriptor.includes(loweredId)) score += 5;
      if (loweredLabel && descriptor.includes(loweredLabel)) score += 4;
      if (profileKey && descriptor.includes(String(profileKey).toLowerCase().replace(/_/g, " "))) score += 2;
      if (element instanceof HTMLInputElement && profileKey === "email" && element.type.toLowerCase() === "email")
        score += 2;
      if (element instanceof HTMLInputElement && profileKey === "phone" && element.type.toLowerCase() === "tel")
        score += 2;
      return { element, score };
    })
    .sort((a, b) => b.score - a.score);

  const best = scored[0];
  if (!best || best.score <= 0) {
    return null;
  }
  return best.element;
}

async function getBridgeContext() {
  return chrome.runtime.sendMessage({ type: "JA_GET_BRIDGE_CONTEXT" });
}

async function reportTelemetry(payload) {
  await chrome.runtime.sendMessage({ type: "JA_TELEMETRY_REPORT", payload });
}

async function requestMappings(context) {
  const result = await chrome.runtime.sendMessage({
    type: "JA_REQUEST_AUTOFILL_MAPPING",
    payload: { pageUrl: window.location.href },
  });
  if (!result?.ok) {
    throw new Error(result?.error || "Autofill mapping request failed.");
  }
  return result.data;
}

let submitEventSentForUrl = false;

function isSubmitControl(target) {
  if (!(target instanceof Element)) {
    return false;
  }
  const submitNode = target.closest("button, input[type='submit']");
  if (!submitNode) {
    return false;
  }
  const label = (
    submitNode.textContent ||
    submitNode.getAttribute("value") ||
    submitNode.getAttribute("aria-label") ||
    ""
  )
    .trim()
    .toLowerCase();
  const typeValue = (submitNode.getAttribute("type") || "").toLowerCase();
  return typeValue === "submit" || label.includes("submit") || label.includes("review and submit");
}

async function reportApplicationEvent(payload) {
  await chrome.runtime.sendMessage({
    type: "JA_APPLICATION_EVENT_REPORT",
    payload,
  });
}

function attachSubmissionObserver() {
  document.addEventListener(
    "click",
    (event) => {
      if (!isSubmitControl(event.target) || submitEventSentForUrl) {
        return;
      }
      submitEventSentForUrl = true;
      reportApplicationEvent({
        pageUrl: window.location.href,
        eventType: "submitted",
        createdAt: new Date().toISOString(),
      }).catch(() => {
        submitEventSentForUrl = false;
      });
    },
    true
  );
}

async function executeFillInTab() {
  const startedAt = new Date().toISOString();
  const contextResponse = await getBridgeContext();
  if (!contextResponse?.ok || !contextResponse?.context) {
    throw new Error(
      "Extension bridge context not found. Open the web app dashboard first so auth/profile can sync."
    );
  }
  const context = contextResponse.context;
  const mappingRaw = await requestMappings(context);
  const mappings = Array.isArray(mappingRaw?.mappings) ? mappingRaw.mappings : [];

  const fieldResults = mappings.map((mapping) => {
    const attemptedValue = String(mapping.suggested_value ?? "");
    const element = findBestElement(
      mapping.field_id,
      mapping.field_label,
      mapping.profile_key,
      mapping.field_type
    );
    if (!attemptedValue) {
      return {
        fieldId: mapping.field_id,
        fieldLabel: mapping.field_label,
        profileKey: mapping.profile_key,
        attemptedValue,
        success: false,
        reason: "empty_value",
        confidence: Number(mapping.confidence ?? 0),
      };
    }
    if (!element) {
      return {
        fieldId: mapping.field_id,
        fieldLabel: mapping.field_label,
        profileKey: mapping.profile_key,
        attemptedValue,
        success: false,
        reason: "field_not_found",
        confidence: Number(mapping.confidence ?? 0),
      };
    }
    const success = setElementValue(element, attemptedValue);
    return {
      fieldId: mapping.field_id,
      fieldLabel: mapping.field_label,
      profileKey: mapping.profile_key,
      attemptedValue,
      success,
      reason: success ? "filled" : "error",
      confidence: Number(mapping.confidence ?? 0),
    };
  });

  const successfulFills = fieldResults.filter((item) => item.success).length;
  const failedFills = fieldResults.length - successfulFills;
  /** @type {ExtensionFillTelemetry} */
  const telemetry = {
    pageUrl: window.location.href,
    startedAt,
    completedAt: new Date().toISOString(),
    totalDetectedFields: Number(mappingRaw?.total_fields ?? 0),
    mappedFields: Number(mappingRaw?.mapped_fields ?? mappings.length),
    successfulFills,
    failedFills,
    mappingPreview: null,
    fieldResults,
    errorMessage: null,
  };
  await reportTelemetry(telemetry);
  return telemetry;
}

function handleWebBridgeSync(event) {
  if (event.source !== window) {
    return;
  }
  const data = event.data;
  if (!data || data.source !== BRIDGE_WEB_SOURCE || data.type !== "JA_SET_BRIDGE_CONTEXT") {
    if (
      data?.source === BRIDGE_WEB_SOURCE &&
      data?.type === "JA_EXECUTE_FILL_FOR_PAGE_REQUEST" &&
      data?.payload?.pageUrl &&
      data?.payload?.requestId
    ) {
      chrome.runtime
        .sendMessage({
          type: "JA_EXECUTE_FILL_FOR_PAGE",
          payload: { pageUrl: data.payload.pageUrl },
        })
        .then((result) => {
          window.postMessage(
            {
              source: BRIDGE_EXTENSION_SOURCE,
              type: "JA_EXECUTE_FILL_FOR_PAGE_RESULT",
              payload: {
                requestId: data.payload.requestId,
                ok: Boolean(result?.ok),
                ...(result?.ok
                  ? { telemetry: result.telemetry }
                  : { error: result?.error || "Failed to execute extension fill." }),
              },
            },
            window.location.origin
          );
        })
        .catch((error) => {
          window.postMessage(
            {
              source: BRIDGE_EXTENSION_SOURCE,
              type: "JA_EXECUTE_FILL_FOR_PAGE_RESULT",
              payload: {
                requestId: data.payload.requestId,
                ok: false,
                error: String(error?.message || error),
              },
            },
            window.location.origin
          );
        });
      return;
    }
    return;
  }
  chrome.runtime.sendMessage({
    type: "JA_STORE_BRIDGE_CONTEXT",
    payload: {
      context: data.payload,
      appOrigin: window.location.origin,
    },
  });
}

window.addEventListener("message", handleWebBridgeSync);
attachSubmissionObserver();

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "JA_REQUEST_CONTEXT_SYNC") {
    window.postMessage(
      {
        source: BRIDGE_EXTENSION_SOURCE,
        type: "JA_REQUEST_CONTEXT_SYNC",
      },
      window.location.origin
    );
    sendResponse({ ok: true });
    return false;
  }

  if (message?.type === "JA_EXECUTE_FILL_IN_TAB") {
    executeFillInTab()
      .then((telemetry) => sendResponse({ ok: true, telemetry }))
      .catch(async (error) => {
        const payload = {
          pageUrl: window.location.href,
          startedAt: new Date().toISOString(),
          completedAt: new Date().toISOString(),
          totalDetectedFields: getFillableElements().length,
          mappedFields: 0,
          successfulFills: 0,
          failedFills: 0,
          mappingPreview: null,
          fieldResults: [],
          errorMessage: String(error.message || error),
        };
        await reportTelemetry(payload);
        sendResponse({ ok: false, error: payload.errorMessage });
      });
    return true;
  }

  if (message?.type === "JA_EXTENSION_TELEMETRY" && message.payload) {
    window.postMessage(
      {
        source: BRIDGE_EXTENSION_SOURCE,
        type: "JA_FILL_TELEMETRY",
        payload: message.payload,
      },
      window.location.origin
    );
    sendResponse({ ok: true });
    return false;
  }

  if (message?.type === "JA_EXTENSION_APPLICATION_EVENT" && message.payload) {
    window.postMessage(
      {
        source: BRIDGE_EXTENSION_SOURCE,
        type: "JA_APPLICATION_EVENT",
        payload: message.payload,
      },
      window.location.origin
    );
    sendResponse({ ok: true });
    return false;
  }

  sendResponse({ ok: false, error: "Unsupported content-script message." });
  return false;
});
