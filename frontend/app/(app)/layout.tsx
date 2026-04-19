export default function AppShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <header className="border-b p-4">
        <span className="font-medium">App shell</span>
        <span className="ml-2 text-sm text-slate-500">
          TODO — session check + nav (PRD)
        </span>
      </header>
      {children}
    </div>
  );
}
