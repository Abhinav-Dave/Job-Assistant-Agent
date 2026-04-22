/**
 * Shared frontend contracts aligned to backend schemas and Phase 10 mocks.
 */

export interface UserPreferences {
  desired_roles: string[];
  target_industries: string[];
  remote_preference: "remote" | "hybrid" | "onsite";
  salary_min: number | null;
}

export interface WorkHistoryItem {
  id: string;
  company: string;
  role: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  bullets: string[];
  display_order: number;
}

export interface EducationItem {
  id: string;
  institution: string;
  degree: string;
  field_of_study: string;
  graduation_year: number | null;
  gpa: string | null;
  display_order: number;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  location: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  province: string | null;
  country: string | null;
  postal_code: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  skills: string[];
  preferences: UserPreferences;
  work_history: WorkHistoryItem[];
  education: EducationItem[];
  onboarding_complete: boolean;
}

export const applicationStatuses = [
  "saved",
  "applied",
  "interviewing",
  "offer",
  "rejected",
] as const;

export type ApplicationStatus = (typeof applicationStatuses)[number];

export interface ApplicationHistoryItem {
  id: string;
  status: ApplicationStatus;
  note: string;
  created_at: string;
}

export interface JobApplication {
  id: string;
  company: string;
  role: string;
  source_url: string;
  status: ApplicationStatus;
  updated_at: string;
  notes: string;
  history: ApplicationHistoryItem[];
}

export const autofillDiagnostics = [
  "none",
  "no_fields_detected",
  "ats_page_not_ready",
  "low_confidence",
] as const;

export type AutofillDiagnosticCode = (typeof autofillDiagnostics)[number];

export interface AutofillRequestPayload {
  page_url: string;
  profile?: UserProfile;
}

export interface AutofillFieldMapping {
  field_id: string;
  field_label: string;
  profile_key: string;
  suggested_value: string;
  confidence: number;
  action: "auto_fill" | "suggest";
}

export interface AutofillResultPayload {
  page_url: string;
  total_fields: number;
  mapped_fields: number;
  fill_rate: number;
  mappings: AutofillFieldMapping[];
  unfilled_fields: string[];
  diagnostic: AutofillDiagnosticCode;
  diagnostic_detail: string | null;
}

export interface MappingRunState {
  isLoading: boolean;
  hasLoaded: boolean;
  hasError: boolean;
  errorMessage: string | null;
  result: AutofillResultPayload | null;
}
