import { AppShellNav } from "@/components/app/app-shell-nav";
import { Phase10AppProvider } from "@/context/phase10-app-context";

export default function AppShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Phase10AppProvider>
      <div className="min-h-screen bg-slate-50">
        <header className="border-b border-slate-200 bg-white px-6 py-4 md:px-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-base font-semibold text-slate-900">Job Assistant Control Plane</p>
              <p className="text-sm text-slate-500">
                Phase 10 static UI (API-ready) with explicit mapping-vs-extension split.
              </p>
            </div>
            <AppShellNav />
          </div>
        </header>
        {children}
      </div>
    </Phase10AppProvider>
  );
}
