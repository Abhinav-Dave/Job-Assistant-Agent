/**
 * All fetch calls to FastAPI — one function per endpoint (PRD Section 9).
 * Base URL: process.env.NEXT_PUBLIC_API_URL (PRD Section 12).
 */

import {
  mockApplications,
  mockAutofillSuccess,
  mockProfile,
} from "@/lib/phase10-mock-data";
import type {
  AutofillRequestPayload,
  AutofillResultPayload,
  JobApplication,
  UserProfile,
} from "@/types";

export const API_BASE =
  typeof process !== "undefined" ? process.env.NEXT_PUBLIC_API_URL ?? "" : "";

/**
 * Phase 10 static adapters.
 * In Phase 11 replace mock returns with real network requests.
 */
export async function getProfile(): Promise<UserProfile> {
  return Promise.resolve(mockProfile);
}

export async function getApplications(): Promise<JobApplication[]> {
  return Promise.resolve(mockApplications);
}

export async function postAutofillMapping(
  payload: AutofillRequestPayload
): Promise<AutofillResultPayload> {
  void payload;
  return Promise.resolve(mockAutofillSuccess);
}
