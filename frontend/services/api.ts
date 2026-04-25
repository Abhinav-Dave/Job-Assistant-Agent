/**
 * FastAPI client wrappers with auth/session-aware error handling.
 */

import { supabase } from "@/lib/supabase";
import type {
  AutofillRequestPayload,
  BackendAutofillResultPayload,
  CreateApplicationRequest,
  JobApplication,
  UpdateApplicationRequest,
  UpdateUserProfileRequest,
  ResumeScoreReport,
  UserProfile,
} from "@/types";

const RAW_API_BASE = typeof process !== "undefined" ? process.env.NEXT_PUBLIC_API_URL ?? "" : "";

function resolveApiBase() {
  const trimmed = (RAW_API_BASE || "").trim();
  if (!trimmed) {
    return "http://127.0.0.1:8000";
  }
  try {
    const parsed = new URL(trimmed);
    const normalizedHost = parsed.hostname === "localhost" ? "127.0.0.1" : parsed.hostname;
    // Guard against accidental frontend-origin API base config.
    if (parsed.port === "3000") {
      return `http://${normalizedHost}:8000`;
    }
    const protocol = parsed.protocol || "http:";
    const port = parsed.port ? `:${parsed.port}` : "";
    return `${protocol}//${normalizedHost}${port}`;
  } catch {
    return trimmed;
  }
}

export const API_BASE = resolveApiBase();

interface ApiErrorPayload {
  error?: string;
  message?: string;
  detail?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly payload: ApiErrorPayload | null;

  constructor(message: string, status: number, payload: ApiErrorPayload | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function buildUrl(path: string) {
  if (!API_BASE) {
    throw new ApiError(
      "NEXT_PUBLIC_API_URL is not configured. Add it to frontend/.env.local.",
      0
    );
  }
  return `${API_BASE}${path}`;
}

function getFallbackApiBase() {
  if (!API_BASE) {
    return null;
  }
  if (API_BASE.includes("localhost")) {
    return API_BASE.replace("localhost", "127.0.0.1");
  }
  if (API_BASE.includes("127.0.0.1")) {
    return API_BASE.replace("127.0.0.1", "localhost");
  }
  return null;
}

async function getAccessToken(): Promise<string> {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession();
    if (error) {
      throw new ApiError(`Failed to read auth session: ${error.message}`, 401);
    }
    if (session?.access_token) {
      return session.access_token;
    }
    await new Promise((resolve) => setTimeout(resolve, 120));
  }
  const { data, error } = await supabase.auth.refreshSession();
  if (error) {
    throw new ApiError(`Failed to refresh auth session: ${error.message}`, 401);
  }
  if (!data.session?.access_token) {
    throw new ApiError("No active session found. Please log in again.", 401);
  }
  return data.session.access_token;
}

async function parseError(response: Response): Promise<ApiError> {
  let payload: ApiErrorPayload | null = null;
  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    payload = null;
  }
  const message =
    payload?.message ??
    payload?.error ??
    `Request failed with status ${response.status}`;
  return new ApiError(message, response.status, payload);
}

async function authFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const makeRequest = async (token: string, baseOverride?: string) =>
    fetch(baseOverride ? `${baseOverride}${path}` : buildUrl(path), {
      ...init,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...(init.headers ?? {}),
      },
      cache: "no-store",
    });

  let response: Response;
  try {
    let token = await getAccessToken();
    response = await makeRequest(token);
    if (response.status === 401) {
      token = await getAccessToken();
      response = await makeRequest(token);
    }
  } catch (error) {
    if (error instanceof TypeError) {
      const fallbackBase = getFallbackApiBase();
      if (fallbackBase) {
        try {
          const token = await getAccessToken();
          response = await makeRequest(token, fallbackBase);
          if (response.status === 401) {
            const refreshedToken = await getAccessToken();
            response = await makeRequest(refreshedToken, fallbackBase);
          }
          if (!response.ok) {
            throw await parseError(response);
          }
          return response;
        } catch (fallbackError) {
          if (fallbackError instanceof ApiError) {
            throw fallbackError;
          }
          if (!(fallbackError instanceof TypeError)) {
            throw fallbackError;
          }
          // Otherwise this was a network error on fallback too.
        }
      }
      throw new ApiError(
        `Failed to reach backend at ${API_BASE || "<missing NEXT_PUBLIC_API_URL>"}${
          fallbackBase ? ` (fallback attempted: ${fallbackBase})` : ""
        }. Network error: ${error.message}`,
        0
      );
    }
    throw error;
  }
  if (!response.ok) {
    throw await parseError(response);
  }
  return response;
}

export async function verifySession(): Promise<{ user_id: string; valid: boolean }> {
  const response = await authFetch("/api/auth/verify", { method: "POST" });
  return (await response.json()) as { user_id: string; valid: boolean };
}

export async function checkApiHealth(): Promise<{ ok: boolean; apiBase: string; detail?: string }> {
  const candidates = [API_BASE, getFallbackApiBase()].filter(
    (value, index, arr): value is string => Boolean(value) && arr.indexOf(value) === index
  );
  let lastFailure: { apiBase: string; detail: string } | null = null;
  for (const base of candidates) {
    try {
      const response = await fetch(`${base}/api/health`, { cache: "no-store" });
      if (response.ok) {
        return { ok: true, apiBase: base };
      }
      lastFailure = { apiBase: base, detail: `Health check returned ${response.status}` };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Network error";
      lastFailure = { apiBase: base, detail: message };
    }
  }
  if (lastFailure) {
    return { ok: false, apiBase: lastFailure.apiBase, detail: lastFailure.detail };
  }
  return { ok: false, apiBase: API_BASE, detail: "No API base candidates available." };
}

export async function getProfile(): Promise<UserProfile> {
  const response = await authFetch("/api/users/me");
  return (await response.json()) as UserProfile;
}

export async function updateProfile(
  payload: UpdateUserProfileRequest
): Promise<UserProfile> {
  const response = await authFetch("/api/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return (await response.json()) as UserProfile;
}

export async function getApplications(): Promise<JobApplication[]> {
  const response = await authFetch("/api/applications");
  return (await response.json()) as JobApplication[];
}

export async function updateApplication(
  applicationId: string,
  payload: UpdateApplicationRequest
): Promise<JobApplication> {
  const response = await authFetch(`/api/applications/${applicationId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return (await response.json()) as JobApplication;
}

export async function createApplication(payload: CreateApplicationRequest): Promise<JobApplication> {
  const response = await authFetch("/api/applications", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return (await response.json()) as JobApplication;
}

export async function postAutofillMapping(
  payload: AutofillRequestPayload
): Promise<BackendAutofillResultPayload> {
  const response = await authFetch("/api/autofill", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return (await response.json()) as BackendAutofillResultPayload;
}

export async function generateAnswer(payload: {
  question: string;
  jd_text?: string | null;
  jd_url?: string | null;
  profile?: UserProfile;
}): Promise<{ answer: string; word_count: number; question: string }> {
  const response = await authFetch("/api/generate/answer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return (await response.json()) as {
    answer: string;
    word_count: number;
    question: string;
  };
}

export async function analyzeResume(payload: {
  jd_text?: string;
  jd_url?: string;
  resume_text?: string;
  resume_file?: File;
}): Promise<{
  match_score: number;
  grade: string;
  summary: string;
  matched_skills: string[];
  missing_skills: string[];
  suggestions: string[];
  jd_key_requirements: string[];
  ats_risk: "low" | "medium" | "high";
  ats_risk_reason: string;
}> {
  const token = await getAccessToken();
  const form = new FormData();
  if (payload.jd_text) {
    form.append("jd_text", payload.jd_text);
  }
  if (payload.jd_url) {
    form.append("jd_url", payload.jd_url);
  }
  if (payload.resume_text) {
    form.append("resume_text", payload.resume_text);
  }
  if (payload.resume_file) {
    form.append("resume_file", payload.resume_file);
  }
  const response = await fetch(buildUrl("/api/resume/analyze"), {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as {
    match_score: number;
    grade: string;
    summary: string;
    matched_skills: string[];
    missing_skills: string[];
    suggestions: string[];
    jd_key_requirements: string[];
    ats_risk: "low" | "medium" | "high";
    ats_risk_reason: string;
  };
}

export async function upsertApplicationScoreReport(
  applicationId: string,
  payload: {
    match_score: number;
    grade: string;
    summary: string;
    matched_skills: string[];
    missing_skills: string[];
    suggestions: string[];
    jd_key_requirements: string[];
    ats_risk: "low" | "medium" | "high";
    ats_risk_reason: string;
  }
): Promise<ResumeScoreReport> {
  const response = await authFetch(`/api/applications/${applicationId}/score-report`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  return (await response.json()) as ResumeScoreReport;
}

export async function getApplicationScoreReport(
  applicationId: string
): Promise<ResumeScoreReport | null> {
  const response = await authFetch(`/api/applications/${applicationId}/score-report`);
  return (await response.json()) as ResumeScoreReport | null;
}
