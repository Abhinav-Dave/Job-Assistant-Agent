"use client";

import { createContext, useContext, type ReactNode } from "react";

type ApplicationContextValue = {
  applications: unknown[];
};

const ApplicationContext = createContext<ApplicationContextValue | undefined>(
  undefined
);

export function ApplicationProvider({ children }: { children: ReactNode }) {
  const value: ApplicationContextValue = { applications: [] };
  return (
    <ApplicationContext.Provider value={value}>
      {children}
    </ApplicationContext.Provider>
  );
}

export function useApplicationContext() {
  const ctx = useContext(ApplicationContext);
  if (!ctx) {
    throw new Error(
      "useApplicationContext must be used within ApplicationProvider"
    );
  }
  return ctx;
}
