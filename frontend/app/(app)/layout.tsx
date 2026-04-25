"use client";

import { useRouter } from "next/navigation";
import { AppShellNav } from "@/components/app/app-shell-nav";
import { Phase10AppProvider } from "@/context/phase10-app-context";
import { supabase } from "@/lib/supabase";

export default function AppShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.replace("/login");
  };

  return (
    <Phase10AppProvider>
      <div className="min-h-screen bg-slate-50">
        <header className="border-b border-slate-200 bg-white px-6 py-4 md:px-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-base font-semibold text-slate-900">Job Assistant Control Plane</p>
              <p className="text-sm text-slate-500">
                Authenticated app with extension bridge handoff.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <AppShellNav />
              <button
                type="button"
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
                onClick={() => void handleSignOut()}
              >
                Sign out
              </button>
            </div>
          </div>
        </header>
        {children}
      </div>
    </Phase10AppProvider>
  );
}
