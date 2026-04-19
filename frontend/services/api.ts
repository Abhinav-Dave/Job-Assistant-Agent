/**
 * All fetch calls to FastAPI — one function per endpoint (PRD Section 9).
 * Base URL: process.env.NEXT_PUBLIC_API_URL (PRD Section 12).
 */

export const API_BASE =
  typeof process !== "undefined" ? process.env.NEXT_PUBLIC_API_URL ?? "" : "";
