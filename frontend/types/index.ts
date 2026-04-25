/**
 * Shared frontend contracts aligned to backend schemas.
 */

export interface UserPreferences {
  desired_roles: string[];
  target_industries: string[];
  remote_preference: "remote" | "hybrid" | "onsite" | null;
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
  field_of_study: string | null;
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
  created_at: string;
  updated_at: string;
}

export interface UpdateUserProfileRequest {
  full_name?: string;
  email?: string;
  phone?: string | null;
  location?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  province?: string | null;
  country?: string | null;
  postal_code?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  skills?: string[];
  preferences?: UserPreferences;
  work_history?: WorkHistoryItem[];
  education?: EducationItem[];
  onboarding_complete?: boolean;
}

export const applicationStatuses = [
  "saved",
  "submitted",
  "response_received",
  "interview_requested",
  "interview_completed",
  "onsite_requested",
  "offer_received",
  "rejected",
  "withdrawn",
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
  user_id: string;
  company: string;
  role: string;
  jd_url: string | null;
  jd_text: string | null;
  status: ApplicationStatus;
  notes: string | null;
  date_applied: string | null;
  last_score: number | null;
  history?: ApplicationHistoryItem[];
  created_at: string;
  updated_at: string;
}

export interface CreateApplicationRequest {
  company: string;
  role: string;
  jd_url?: string | null;
  jd_text?: string | null;
  status?: ApplicationStatus;
  notes?: string | null;
  date_applied?: string | null;
}

export interface UpdateApplicationRequest {
  company?: string;
  role?: string;
  jd_url?: string | null;
  jd_text?: string | null;
  notes?: string | null;
  status?: ApplicationStatus;
  date_applied?: string | null;
  last_score?: number | null;
}

export interface ResumeScoreReport {
  application_id: string;
  user_id: string;
  match_score: number;
  grade: string;
  summary: string;
  matched_skills: string[];
  missing_skills: string[];
  suggestions: string[];
  jd_key_requirements: string[];
  ats_risk: "low" | "medium" | "high";
  ats_risk_reason: string;
  created_at: string;
  updated_at: string;
}

export const autofillDiagnostics = [
  "none",
  "no_fields_detected",
  "ats_page_not_ready",
  "low_confidence",
  "request_failed",
] as const;

export type AutofillDiagnosticCode = (typeof autofillDiagnostics)[number];

export interface AutofillRequestPayload {
  page_url: string;
  profile?: UserProfile;
}

export interface BackendAutofillFieldMapping {
  field_id: string;
  field_label: string;
  field_type: string;
  profile_key: string;
  suggested_value: string;
  confidence: number;
}

export interface BackendAutofillResultPayload {
  fill_rate: number;
  total_fields: number;
  mapped_fields: number;
  mappings: BackendAutofillFieldMapping[];
  unfilled_fields: string[];
}

export interface AutofillFieldMapping extends BackendAutofillFieldMapping {
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
