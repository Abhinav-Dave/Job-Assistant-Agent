"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  mockApplications,
  mockAutofillAtsNotReady,
  mockAutofillNoFields,
  mockAutofillSuccess,
  mockProfile,
} from "@/lib/phase10-mock-data";
import type {
  AutofillResultPayload,
  JobApplication,
  MappingRunState,
  UserProfile,
} from "@/types";

interface Phase10AppContextValue {
  profile: UserProfile;
  applications: JobApplication[];
  selectedApplicationId: string;
  mappingState: MappingRunState;
  editedMappingValues: Record<string, string>;
  setSelectedApplicationId: (applicationId: string) => void;
  updateProfileField: (field: keyof UserProfile, value: string) => void;
  updateApplicationNotes: (applicationId: string, notes: string) => void;
  runMappingPreview: (mode?: "success" | "no_fields" | "ats_not_ready") => Promise<void>;
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

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const buildResultByMode = (
  mode: "success" | "no_fields" | "ats_not_ready"
): AutofillResultPayload => {
  if (mode === "no_fields") {
    return mockAutofillNoFields;
  }
  if (mode === "ats_not_ready") {
    return mockAutofillAtsNotReady;
  }
  return mockAutofillSuccess;
};

export function Phase10AppProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<UserProfile>(mockProfile);
  const [applications, setApplications] = useState<JobApplication[]>(mockApplications);
  const [selectedApplicationId, setSelectedApplicationId] = useState<string>(
    mockApplications[0]?.id ?? ""
  );
  const [mappingState, setMappingState] = useState<MappingRunState>(initialMappingState);
  const [editedMappingValues, setEditedMappingValues] = useState<Record<string, string>>({});

  const selectedApplication = useMemo(
    () => applications.find((application) => application.id === selectedApplicationId) ?? null,
    [applications, selectedApplicationId]
  );

  const updateProfileField = useCallback((field: keyof UserProfile, value: string) => {
    setProfile((current) => ({
      ...current,
      [field]: value,
    }));
  }, []);

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

  const runMappingPreview = useCallback(
    async (mode: "success" | "no_fields" | "ats_not_ready" = "success") => {
      setMappingState({
        isLoading: true,
        hasLoaded: false,
        hasError: false,
        errorMessage: null,
        result: null,
      });
      await sleep(700);
      const result = buildResultByMode(mode);
      const hasError = result.diagnostic !== "none" && result.mapped_fields === 0;
      setMappingState({
        isLoading: false,
        hasLoaded: true,
        hasError,
        errorMessage: hasError ? result.diagnostic_detail ?? "Mapping did not return fields." : null,
        result,
      });
      setEditedMappingValues(
        Object.fromEntries(result.mappings.map((mapping) => [mapping.field_id, mapping.suggested_value]))
      );
    },
    []
  );

  const setEditedMappingValue = useCallback((fieldId: string, value: string) => {
    setEditedMappingValues((current) => ({
      ...current,
      [fieldId]: value,
    }));
  }, []);

  const contextValue = useMemo(
    () => ({
      profile,
      applications,
      selectedApplicationId,
      mappingState,
      editedMappingValues,
      setSelectedApplicationId,
      updateProfileField,
      updateApplicationNotes,
      runMappingPreview,
      setEditedMappingValue,
      selectedApplication,
    }),
    [
      profile,
      applications,
      selectedApplicationId,
      mappingState,
      editedMappingValues,
      updateProfileField,
      updateApplicationNotes,
      runMappingPreview,
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
