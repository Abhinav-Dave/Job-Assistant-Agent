"use client";

import { useApplicationContext } from "@/context/ApplicationContext";

export function useApplications() {
  return useApplicationContext();
}
