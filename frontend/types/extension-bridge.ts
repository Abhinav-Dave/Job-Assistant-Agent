import type { AutofillResultPayload, UserProfile } from "@/types";

export const BRIDGE_SOURCE_WEB = "job-assistant-web";
export const BRIDGE_SOURCE_EXTENSION = "job-assistant-extension";

export interface BridgeContextPayload {
  apiBaseUrl: string;
  accessToken: string;
  profile?: UserProfile;
  syncedAt: string;
}

export interface ExtensionFieldFillResult {
  fieldId: string;
  fieldLabel: string;
  profileKey: string;
  attemptedValue: string;
  success: boolean;
  reason:
    | "filled"
    | "field_not_found"
    | "incompatible_field"
    | "read_only"
    | "empty_value"
    | "error";
  confidence: number;
}

export interface ExtensionFillTelemetry {
  pageUrl: string;
  startedAt: string;
  completedAt: string;
  totalDetectedFields: number;
  mappedFields: number;
  successfulFills: number;
  failedFills: number;
  mappingPreview: AutofillResultPayload | null;
  fieldResults: ExtensionFieldFillResult[];
  errorMessage: string | null;
  telemetryDispatchError?: string | null;
}

export interface ExtensionApplicationEvent {
  pageUrl: string;
  eventType: "submitted";
  createdAt: string;
}

export interface WebToExtensionSyncMessage {
  source: typeof BRIDGE_SOURCE_WEB;
  type: "JA_SET_BRIDGE_CONTEXT";
  payload: BridgeContextPayload;
}

export interface WebToExtensionExecuteFillMessage {
  source: typeof BRIDGE_SOURCE_WEB;
  type: "JA_EXECUTE_FILL_FOR_PAGE_REQUEST";
  payload: {
    pageUrl: string;
    requestId: string;
  };
}

export interface ExtensionToWebTelemetryMessage {
  source: typeof BRIDGE_SOURCE_EXTENSION;
  type: "JA_FILL_TELEMETRY";
  payload: ExtensionFillTelemetry;
}

export interface ExtensionToWebApplicationEventMessage {
  source: typeof BRIDGE_SOURCE_EXTENSION;
  type: "JA_APPLICATION_EVENT";
  payload: ExtensionApplicationEvent;
}

export interface ExtensionToWebExecuteFillResultMessage {
  source: typeof BRIDGE_SOURCE_EXTENSION;
  type: "JA_EXECUTE_FILL_FOR_PAGE_RESULT";
  payload: {
    requestId: string;
    ok: boolean;
    error?: string;
    telemetry?: ExtensionFillTelemetry;
  };
}

export type BridgeWindowMessage =
  | WebToExtensionSyncMessage
  | WebToExtensionExecuteFillMessage
  | ExtensionToWebTelemetryMessage
  | ExtensionToWebApplicationEventMessage
  | ExtensionToWebExecuteFillResultMessage;
