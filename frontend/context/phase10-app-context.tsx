"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { supabase } from "@/lib/supabase";
import {
  ApiError,
  analyzeResume,
  checkApiHealth,
  createApplication,
  getApplicationScoreReport,
  getApplications,
  getProfile,
  postAutofillMapping,
  upsertApplicationScoreReport,
  updateApplication,
  updateProfile,
} from "@/services/api";
import {
  BRIDGE_SOURCE_EXTENSION,
  BRIDGE_SOURCE_WEB,
  type BridgeWindowMessage,
  type ExtensionApplicationEvent,
  type ExtensionFillTelemetry,
  type WebToExtensionSyncMessage,
} from "@/types/extension-bridge";
import type {
  AutofillDiagnosticCode,
  AutofillResultPayload,
  BackendAutofillResultPayload,
  EducationItem,
  JobApplication,
  MappingRunState,
  ResumeScoreReport,
  UserProfile,
  WorkHistoryItem,
} from "@/types";

interface Phase10AppContextValue {
  profile: UserProfile | null;
  applications: JobApplication[];
  authLoading: boolean;
  dataLoading: boolean;
  globalError: string | null;
  apiHealth: { ok: boolean; apiBase: string; detail?: string } | null;
  profileSaveState: {
    isSaving: boolean;
    error: string | null;
  };
  extensionTelemetry: ExtensionFillTelemetry[];
  resumeFile: File | null;
  selectedApplicationId: string;
  mappingState: MappingRunState;
  editedMappingValues: Record<string, string>;
  initializeApp: () => Promise<void>;
  setSelectedApplicationId: (applicationId: string) => void;
  updateProfileField: (field: keyof UserProfile, value: string) => void;
  updateWorkHistoryItem: (
    workId: string,
    field: keyof WorkHistoryItem,
    value: string | boolean | string[] | null
  ) => void;
  addWorkHistoryItem: () => void;
  deleteWorkHistoryItem: (workId: string) => void;
  updateEducationItem: (
    educationId: string,
    field: keyof EducationItem,
    value: string | number | null
  ) => void;
  addEducationItem: () => void;
  deleteEducationItem: (educationId: string) => void;
  saveProfile: () => Promise<void>;
  updateApplicationNotes: (applicationId: string, notes: string) => void;
  saveApplicationNotes: (applicationId: string) => Promise<boolean>;
  markApplicationComplete: (applicationId: string) => Promise<boolean>;
  setResumeFile: (file: File | null) => void;
  scoreResumeForApplication: (
    applicationId: string
  ) => Promise<{
    ok: boolean;
    error?: string;
    result?: {
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
  }>;
  fetchScoreReportForApplication: (applicationId: string) => Promise<ResumeScoreReport | null>;
  runMappingPreview: (pageUrl: string) => Promise<void>;
  executeFillInBrowserTab: (pageUrl: string) => Promise<{
    ok: boolean;
    error?: string;
    telemetry?: ExtensionFillTelemetry;
  }>;
  setEditedMappingValue: (fieldId: string, value: string) => void;
  selectedApplication: JobApplication | null;
}

const initialMappingState: MappingRunState = {
  isLoading: false,
  hasLoaded: false,
  hasError: false,
  errorMessage: null,
  result: null,
};

const Phase10AppContext = createContext<Phase10AppContextValue | null>(null);
const PROFILE_DRAFT_STORAGE_KEY = "ja_profile_draft_v1";

const confidenceToAction = (confidence: number) => (confidence >= 0.85 ? "auto_fill" : "suggest");

const deriveDiagnostic = (
  result: BackendAutofillResultPayload
): { diagnostic: AutofillDiagnosticCode; detail: string | null } => {
  if (result.total_fields === 0) {
    return {
      diagnostic: "no_fields_detected",
      detail:
        "No form fields were detected. The page may require authentication or in-tab progression.",
    };
  }
  if (result.mapped_fields === 0) {
    return {
      diagnostic: "ats_page_not_ready",
      detail:
        "Fields were detected but none were mapped. Try progressing in-tab and rerun mapping preview.",
    };
  }
  if (result.mappings.some((mapping) => mapping.confidence < 0.85)) {
    return {
      diagnostic: "low_confidence",
      detail:
        "Some fields are suggestions only. Confirm values before executing fill in browser tab.",
    };
  }
  return { diagnostic: "none", detail: null };
};

const mapAutofillResponse = (
  pageUrl: string,
  result: BackendAutofillResultPayload
): AutofillResultPayload => {
  const diag = deriveDiagnostic(result);
  return {
    page_url: pageUrl,
    total_fields: result.total_fields,
    mapped_fields: result.mapped_fields,
    fill_rate: result.fill_rate,
    mappings: result.mappings.map((mapping) => ({
      ...mapping,
      action: confidenceToAction(mapping.confidence),
    })),
    unfilled_fields: result.unfilled_fields,
    diagnostic: diag.diagnostic,
    diagnostic_detail: diag.detail,
  };
};

const mapApiApplication = (application: JobApplication): JobApplication => ({
  ...application,
  history:
    application.history ??
    [
      {
        id: `initial-${application.id}`,
        status: application.status,
        note: "Loaded from backend",
        created_at: application.created_at,
      },
    ],
});

const normalizeUrl = (value: string) => value.trim().toLowerCase();

const inferCompanyFromUrl = (pageUrl: string) => {
  try {
    const hostname = new URL(pageUrl).hostname.replace(/^www\./, "");
    const root = hostname.split(".")[0] || "Unknown";
    return root.replace(/[-_]/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
  } catch {
    return "Unknown";
  }
};

export function Phase10AppProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [authLoading, setAuthLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [apiHealth, setApiHealth] = useState<{
    ok: boolean;
    apiBase: string;
    detail?: string;
  } | null>(null);
  const [profileSaveState, setProfileSaveState] = useState({
    isSaving: false,
    error: null as string | null,
  });
  const [extensionTelemetry, setExtensionTelemetry] = useState<ExtensionFillTelemetry[]>([]);
  const [resumeFile, setResumeFileState] = useState<File | null>(null);
  const [selectedApplicationId, setSelectedApplicationId] = useState<string>("");
  const [mappingState, setMappingState] = useState<MappingRunState>(initialMappingState);
  const [editedMappingValues, setEditedMappingValues] = useState<Record<string, string>>({});
  const [hasProfileDraftChanges, setHasProfileDraftChanges] = useState(false);

  const selectedApplication = useMemo(
    () => applications.find((application) => application.id === selectedApplicationId) ?? null,
    [applications, selectedApplicationId]
  );

  const initializeApp = useCallback(async () => {
    setAuthLoading(true);
    setDataLoading(true);
    setGlobalError(null);
    try {
      const health = await checkApiHealth();
      setApiHealth(health);
      const [nextProfile, nextApplications] = await Promise.all([
        getProfile(),
        getApplications(),
      ]);
      let resolvedProfile = nextProfile;
      if (typeof window !== "undefined") {
        const draftRaw = window.sessionStorage.getItem(PROFILE_DRAFT_STORAGE_KEY);
        if (draftRaw) {
          try {
            const draft = JSON.parse(draftRaw) as UserProfile;
            if (draft?.id === nextProfile.id) {
              resolvedProfile = draft;
              setHasProfileDraftChanges(true);
            }
          } catch {
            window.sessionStorage.removeItem(PROFILE_DRAFT_STORAGE_KEY);
          }
        }
      }
      setProfile(resolvedProfile);
      const normalizedApps = nextApplications.map(mapApiApplication);
      setApplications(normalizedApps);
      setSelectedApplicationId((current) => current || normalizedApps[0]?.id || "");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setGlobalError("Session expired. Please log in again.");
        setProfile(null);
        setApplications([]);
      } else {
        const message =
          error instanceof Error ? error.message : "Failed to load authenticated app data.";
        setGlobalError(message);
      }
    } finally {
      setAuthLoading(false);
      setDataLoading(false);
    }
  }, []);

  useEffect(() => {
    void initializeApp();
  }, [initializeApp]);

  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED" || event === "INITIAL_SESSION") {
        void initializeApp();
      }
      if (event === "SIGNED_OUT") {
        setProfile(null);
        setApplications([]);
        setGlobalError("Session expired. Please log in again.");
        setSelectedApplicationId("");
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [initializeApp]);

  const updateProfileField = useCallback((field: keyof UserProfile, value: string) => {
    setProfile((current) =>
      current
        ? {
            ...current,
            [field]: value,
          }
        : current
    );
    setHasProfileDraftChanges(true);
  }, []);

  const updateWorkHistoryItem = useCallback(
    (
      workId: string,
      field: keyof WorkHistoryItem,
      value: string | boolean | string[] | null
    ) => {
      setProfile((current) =>
        current
          ? {
              ...current,
              work_history: current.work_history.map((item) =>
                item.id === workId ? { ...item, [field]: value } : item
              ),
            }
          : current
      );
      setHasProfileDraftChanges(true);
    },
    []
  );

  const addWorkHistoryItem = useCallback(() => {
    setProfile((current) => {
      if (!current) {
        return current;
      }
      const nextOrder = current.work_history.length;
      const today = new Date();
      const yyyyMm = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
      return {
        ...current,
        work_history: [
          ...current.work_history,
          {
            id: crypto.randomUUID(),
            company: "",
            role: "",
            start_date: yyyyMm,
            end_date: null,
            is_current: false,
            bullets: [],
            display_order: nextOrder,
          },
        ],
      };
    });
    setHasProfileDraftChanges(true);
  }, []);

  const deleteWorkHistoryItem = useCallback((workId: string) => {
    setProfile((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        work_history: current.work_history
          .filter((item) => item.id !== workId)
          .map((item, index) => ({ ...item, display_order: index })),
      };
    });
    setHasProfileDraftChanges(true);
  }, []);

  const updateEducationItem = useCallback(
    (
      educationId: string,
      field: keyof EducationItem,
      value: string | number | null
    ) => {
      setProfile((current) =>
        current
          ? {
              ...current,
              education: current.education.map((item) =>
                item.id === educationId ? { ...item, [field]: value } : item
              ),
            }
          : current
      );
      setHasProfileDraftChanges(true);
    },
    []
  );

  const addEducationItem = useCallback(() => {
    setProfile((current) => {
      if (!current) {
        return current;
      }
      const nextOrder = current.education.length;
      return {
        ...current,
        education: [
          ...current.education,
          {
            id: crypto.randomUUID(),
            institution: "",
            degree: "",
            field_of_study: null,
            graduation_year: null,
            gpa: null,
            display_order: nextOrder,
          },
        ],
      };
    });
    setHasProfileDraftChanges(true);
  }, []);

  const deleteEducationItem = useCallback((educationId: string) => {
    setProfile((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        education: current.education
          .filter((item) => item.id !== educationId)
          .map((item, index) => ({ ...item, display_order: index })),
      };
    });
    setHasProfileDraftChanges(true);
  }, []);

  const saveProfile = useCallback(async () => {
    if (!profile) {
      return;
    }
    setProfileSaveState({ isSaving: true, error: null });
    try {
      const sanitizedWorkHistory = profile.work_history
        .map((item) => ({
          ...item,
          company: item.company.trim(),
          role: item.role.trim(),
          start_date: item.start_date.trim(),
        }))
        .filter((item) => item.company && item.role && item.start_date);
      const sanitizedEducation = profile.education
        .map((item) => ({
          ...item,
          institution: item.institution.trim(),
          degree: item.degree.trim(),
        }))
        .filter((item) => item.institution && item.degree);

      const updated = await updateProfile({
        full_name: profile.full_name,
        email: profile.email,
        phone: profile.phone,
        location: profile.location,
        address_line1: profile.address_line1,
        address_line2: profile.address_line2,
        city: profile.city,
        province: profile.province,
        country: profile.country,
        postal_code: profile.postal_code,
        linkedin_url: profile.linkedin_url,
        portfolio_url: profile.portfolio_url,
        skills: profile.skills,
        preferences: profile.preferences,
        work_history: sanitizedWorkHistory,
        education: sanitizedEducation,
        onboarding_complete: profile.onboarding_complete,
      });
      setProfile(updated);
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem(PROFILE_DRAFT_STORAGE_KEY);
      }
      setHasProfileDraftChanges(false);
      setProfileSaveState({ isSaving: false, error: null });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save profile.";
      setProfileSaveState({ isSaving: false, error: message });
    }
  }, [profile]);

  useEffect(() => {
    if (!profile || typeof window === "undefined") {
      return;
    }
    if (!hasProfileDraftChanges) {
      return;
    }
    window.sessionStorage.setItem(PROFILE_DRAFT_STORAGE_KEY, JSON.stringify(profile));
  }, [profile, hasProfileDraftChanges]);

  const updateApplicationNotes = useCallback((applicationId: string, notes: string) => {
    setApplications((current) =>
      current.map((application) =>
        application.id === applicationId
          ? {
              ...application,
              notes,
              updated_at: new Date().toISOString(),
            }
          : application
      )
    );
  }, []);

  const saveApplicationNotes = useCallback(async (applicationId: string) => {
    const application = applications.find((item) => item.id === applicationId);
    if (!application) {
      return false;
    }
    try {
      const updated = await updateApplication(applicationId, { notes: application.notes ?? "" });
      setApplications((current) =>
        current.map((item) => (item.id === applicationId ? mapApiApplication(updated) : item))
      );
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save notes.";
      setGlobalError(message);
      return false;
    }
  }, [applications]);

  const markApplicationComplete = useCallback(
    async (applicationId: string) => {
      try {
        const updated = await updateApplication(applicationId, {
          status: "submitted",
          date_applied: new Date().toISOString().slice(0, 10),
        });
        setApplications((current) =>
          current.map((item) => (item.id === applicationId ? mapApiApplication(updated) : item))
        );
        return true;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to mark application complete.";
        setGlobalError(message);
        return false;
      }
    },
    []
  );

  const setResumeFile = useCallback((file: File | null) => {
    setResumeFileState(file);
  }, []);

  const scoreResumeForApplication = useCallback(
    async (applicationId: string) => {
      const target = applications.find((item) => item.id === applicationId);
      if (!target) {
        return { ok: false, error: "No application selected for scoring." };
      }
      if (!resumeFile) {
        return { ok: false, error: "Upload a resume in Profile before scoring jobs." };
      }
      try {
        const result = await analyzeResume({
          jd_url: target.jd_url ?? undefined,
          jd_text: target.jd_text ?? undefined,
          resume_file: resumeFile,
        });
        await updateApplication(applicationId, { last_score: result.match_score });
        await upsertApplicationScoreReport(applicationId, result);
        setApplications((current) =>
          current.map((item) =>
            item.id === applicationId
              ? { ...item, last_score: result.match_score, updated_at: new Date().toISOString() }
              : item
          )
        );
        return { ok: true, result };
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to score resume.";
        return { ok: false, error: message };
      }
    },
    [applications, resumeFile]
  );

  const fetchScoreReportForApplication = useCallback(async (applicationId: string) => {
    try {
      return await getApplicationScoreReport(applicationId);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to fetch score report.";
      setGlobalError(message);
      return null;
    }
  }, []);

  const findApplicationByUrl = useCallback(
    (pageUrl: string) =>
      applications.find(
        (application) => application.jd_url && normalizeUrl(application.jd_url) === normalizeUrl(pageUrl)
      ) ?? null,
    [applications]
  );

  const ensureApplicationForPage = useCallback(
    async (pageUrl: string, seedNote: string): Promise<JobApplication | null> => {
      const existing = findApplicationByUrl(pageUrl) ?? selectedApplication;
      if (existing) {
        return existing;
      }
      try {
        const created = await createApplication({
          company: inferCompanyFromUrl(pageUrl),
          role: "Application in progress",
          jd_url: pageUrl,
          notes: seedNote,
          status: "saved",
        });
        const mapped = mapApiApplication(created);
        setApplications((current) => [mapped, ...current]);
        setSelectedApplicationId(mapped.id);
        return mapped;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to create application.";
        setGlobalError(message);
        return null;
      }
    },
    [findApplicationByUrl, selectedApplication]
  );

  const runMappingPreview = useCallback(async (pageUrl: string) => {
    if (!profile) {
      setMappingState({
        isLoading: false,
        hasLoaded: true,
        hasError: true,
        errorMessage: "Profile is not loaded yet. Log in and refresh mapping preview.",
        result: null,
      });
      return;
    }
    const trimmedUrl = pageUrl.trim();
    if (!trimmedUrl) {
      setMappingState({
        isLoading: false,
        hasLoaded: true,
        hasError: true,
        errorMessage: "A valid URL is required before running mapping preview.",
        result: null,
      });
      return;
    }
    setMappingState({
      isLoading: true,
      hasLoaded: false,
      hasError: false,
      errorMessage: null,
      result: null,
    });
    try {
      const backendResult = await postAutofillMapping({ page_url: trimmedUrl, profile });
      const mappedResult = mapAutofillResponse(trimmedUrl, backendResult);
      const hasError = mappedResult.diagnostic !== "none" && mappedResult.mapped_fields === 0;
      setMappingState({
        isLoading: false,
        hasLoaded: true,
        hasError,
        errorMessage: hasError
          ? mappedResult.diagnostic_detail ?? "Mapping preview did not return editable fields."
          : null,
        result: mappedResult,
      });
      setEditedMappingValues(
        Object.fromEntries(
          mappedResult.mappings.map((mapping) => [mapping.field_id, mapping.suggested_value])
        )
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to run mapping preview.";
      setMappingState({
        isLoading: false,
        hasLoaded: true,
        hasError: true,
        errorMessage: message,
        result: {
          page_url: trimmedUrl,
          total_fields: 0,
          mapped_fields: 0,
          fill_rate: 0,
          mappings: [],
          unfilled_fields: [],
          diagnostic: "request_failed",
          diagnostic_detail: message,
        },
      });
    }
  }, [profile]);

  const executeFillInBrowserTab = useCallback(
    async (pageUrl: string) => {
      const requestId = `req-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      return await new Promise<{
        ok: boolean;
        error?: string;
        telemetry?: ExtensionFillTelemetry;
      }>((resolve) => {
        const timeout = window.setTimeout(() => {
          window.removeEventListener("message", onMessage);
          resolve({
            ok: false,
            error:
              "No extension response received. Ensure the extension is loaded and this dashboard tab stays open.",
          });
        }, 25000);

        const onMessage = (event: MessageEvent<BridgeWindowMessage>) => {
          if (event.source !== window) {
            return;
          }
          const data = event.data;
          if (
            !data ||
            data.source !== BRIDGE_SOURCE_EXTENSION ||
            data.type !== "JA_EXECUTE_FILL_FOR_PAGE_RESULT"
          ) {
            return;
          }
          if (data.payload.requestId !== requestId) {
            return;
          }
          window.clearTimeout(timeout);
          window.removeEventListener("message", onMessage);
          resolve({
            ok: data.payload.ok,
            ...(data.payload.ok
              ? { telemetry: data.payload.telemetry }
              : { error: data.payload.error || "Failed to execute extension fill." }),
          });
        };

        window.addEventListener("message", onMessage);
        window.postMessage(
          {
            source: BRIDGE_SOURCE_WEB,
            type: "JA_EXECUTE_FILL_FOR_PAGE_REQUEST",
            payload: {
              pageUrl,
              requestId,
            },
          },
          window.location.origin
        );
      });
    },
    []
  );

  const setEditedMappingValue = useCallback((fieldId: string, value: string) => {
    setEditedMappingValues((current) => ({
      ...current,
      [fieldId]: value,
    }));
  }, []);

  useEffect(() => {
    const syncBridgeContext = async () => {
      if (typeof window === "undefined") {
        return;
      }
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) {
        return;
      }
      const message: WebToExtensionSyncMessage = {
        source: BRIDGE_SOURCE_WEB,
        type: "JA_SET_BRIDGE_CONTEXT",
        payload: {
          apiBaseUrl: process.env.NEXT_PUBLIC_API_URL ?? "",
          accessToken: session.access_token,
          ...(profile ? { profile } : {}),
          syncedAt: new Date().toISOString(),
        },
      };
      window.postMessage(message, window.location.origin);
    };
    void syncBridgeContext();
  }, [profile]);

  useEffect(() => {
    const handleContextSyncRequest = (
      event: MessageEvent<{ source?: string; type?: string }>
    ) => {
      if (event.source !== window) {
        return;
      }
      if (
        event.data?.source !== BRIDGE_SOURCE_EXTENSION ||
        event.data?.type !== "JA_REQUEST_CONTEXT_SYNC"
      ) {
        return;
      }
      void (async () => {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session?.access_token) {
          return;
        }
        const message: WebToExtensionSyncMessage = {
          source: BRIDGE_SOURCE_WEB,
          type: "JA_SET_BRIDGE_CONTEXT",
          payload: {
            apiBaseUrl: process.env.NEXT_PUBLIC_API_URL ?? "",
            accessToken: session.access_token,
            ...(profile ? { profile } : {}),
            syncedAt: new Date().toISOString(),
          },
        };
        window.postMessage(message, window.location.origin);
      })();
    };

    window.addEventListener("message", handleContextSyncRequest);
    return () => window.removeEventListener("message", handleContextSyncRequest);
  }, [profile]);

  useEffect(() => {
    const handleMessage = (event: MessageEvent<BridgeWindowMessage>) => {
      if (event.source !== window) {
        return;
      }
      const data = event.data;
      if (!data || data.source !== BRIDGE_SOURCE_EXTENSION || !data.payload) {
        return;
      }
      if (data.type === "JA_FILL_TELEMETRY") {
        const payload = data.payload as ExtensionFillTelemetry;
        setExtensionTelemetry((current) => [payload, ...current].slice(0, 20));
        const note = `Extension fill: ${payload.successfulFills}/${payload.mappedFields} mapped fields`;
        void (async () => {
          const application = await ensureApplicationForPage(payload.pageUrl, note);
          if (!application) {
            return;
          }
          try {
            const nextNotes = `${application.notes ?? ""}\n[${new Date(payload.completedAt).toLocaleString()}] ${note}`.trim();
            const updated = await updateApplication(application.id, {
              notes: nextNotes,
              status: application.status,
            });
            const mapped = mapApiApplication(updated);
            setApplications((current) =>
              current.map((item) => (item.id === mapped.id ? mapped : item))
            );
          } catch (error) {
            const message = error instanceof Error ? error.message : "Failed to persist fill telemetry.";
            setGlobalError(message);
          }
        })();
        return;
      }

      if (data.type === "JA_APPLICATION_EVENT") {
        const payload = data.payload as ExtensionApplicationEvent;
        void (async () => {
          const application = await ensureApplicationForPage(
            payload.pageUrl,
            "Application in progress"
          );
          if (!application) {
            return;
          }
          try {
            const updated = await updateApplication(application.id, {
              status: "submitted",
              date_applied: new Date(payload.createdAt).toISOString().slice(0, 10),
              notes: `${application.notes ?? ""}\n[${new Date(payload.createdAt).toLocaleString()}] Submit action detected in extension.`.trim(),
            });
            const mapped = mapApiApplication(updated);
            setApplications((current) =>
              current.map((item) => (item.id === mapped.id ? mapped : item))
            );
          } catch (error) {
            const message =
              error instanceof Error ? error.message : "Failed to persist submit event.";
            setGlobalError(message);
          }
        })();
      }
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [ensureApplicationForPage]);

  const contextValue = useMemo(
    () => ({
      profile,
      applications,
      authLoading,
      dataLoading,
      globalError,
      apiHealth,
      profileSaveState,
      extensionTelemetry,
      resumeFile,
      selectedApplicationId,
      mappingState,
      editedMappingValues,
      initializeApp,
      setSelectedApplicationId,
      updateProfileField,
      updateWorkHistoryItem,
      addWorkHistoryItem,
      deleteWorkHistoryItem,
      updateEducationItem,
      addEducationItem,
      deleteEducationItem,
      saveProfile,
      updateApplicationNotes,
      saveApplicationNotes,
      markApplicationComplete,
      setResumeFile,
      scoreResumeForApplication,
      fetchScoreReportForApplication,
      runMappingPreview,
      executeFillInBrowserTab,
      setEditedMappingValue,
      selectedApplication,
    }),
    [
      profile,
      applications,
      authLoading,
      dataLoading,
      globalError,
      apiHealth,
      profileSaveState,
      extensionTelemetry,
      resumeFile,
      selectedApplicationId,
      mappingState,
      editedMappingValues,
      initializeApp,
      updateProfileField,
      updateWorkHistoryItem,
      addWorkHistoryItem,
      deleteWorkHistoryItem,
      updateEducationItem,
      addEducationItem,
      deleteEducationItem,
      saveProfile,
      updateApplicationNotes,
      saveApplicationNotes,
      markApplicationComplete,
      setResumeFile,
      scoreResumeForApplication,
      fetchScoreReportForApplication,
      runMappingPreview,
      executeFillInBrowserTab,
      setEditedMappingValue,
      selectedApplication,
    ]
  );

  return <Phase10AppContext.Provider value={contextValue}>{children}</Phase10AppContext.Provider>;
}

export function usePhase10App() {
  const context = useContext(Phase10AppContext);
  if (!context) {
    throw new Error("usePhase10App must be used inside Phase10AppProvider.");
  }
  return context;
}
