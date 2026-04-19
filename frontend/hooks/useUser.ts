"use client";

import { useUserContext } from "@/context/UserContext";

export function useUser() {
  return useUserContext();
}
