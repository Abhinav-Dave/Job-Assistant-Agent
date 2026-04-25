"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const check = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      router.replace(session?.access_token ? "/dashboard" : "/login");
    };
    void check();
  }, [router]);

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <p className="text-sm text-slate-600">Checking session...</p>
    </main>
  );
}
