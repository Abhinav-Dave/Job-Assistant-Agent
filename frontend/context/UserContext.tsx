"use client";

import { createContext, useContext, type ReactNode } from "react";

type UserContextValue = {
  user: null;
  profile: null;
};

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const value: UserContextValue = { user: null, profile: null };
  return (
    <UserContext.Provider value={value}>{children}</UserContext.Provider>
  );
}

export function useUserContext() {
  const ctx = useContext(UserContext);
  if (!ctx) {
    throw new Error("useUserContext must be used within UserProvider");
  }
  return ctx;
}
