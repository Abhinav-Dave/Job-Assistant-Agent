"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { usePhase10App } from "@/context/phase10-app-context";
import type { ApplicationStatus } from "@/types";

const statusTone: Record<ApplicationStatus, string> = {
  saved: "bg-slate-100 text-slate-700",
  submitted: "bg-blue-100 text-blue-700",
  response_received: "bg-cyan-100 text-cyan-700",
  interview_requested: "bg-amber-100 text-amber-800",
  interview_completed: "bg-amber-200 text-amber-900",
  onsite_requested: "bg-violet-100 text-violet-700",
  offer_received: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-700",
  withdrawn: "bg-slate-200 text-slate-700",
};

export function ApplicationTrackerDashboard() {
  const {
    applications,
    authLoading,
    dataLoading,
    globalError,
    apiHealth,
  } = usePhase10App();
  const mostRecentTen = [...applications]
    .sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))
    .slice(0, 10);
  const statusCounts = applications.reduce<Record<ApplicationStatus, number>>(
    (accumulator, application) => ({
      ...accumulator,
      [application.status]: accumulator[application.status] + 1,
    }),
    {
      saved: 0,
      submitted: 0,
      response_received: 0,
      interview_requested: 0,
      interview_completed: 0,
      onsite_requested: 0,
      offer_received: 0,
      rejected: 0,
      withdrawn: 0,
    }
  );

  const getDisplayStatus = (application: (typeof applications)[number]) => {
    const notes = (application.notes ?? "").toLowerCase();
    if (application.status === "saved" && notes.includes("extension fill")) {
      return "in_progress";
    }
    return application.status;
  };

  return (
    <main className="space-y-6 p-6 md:p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900">Application Tracker Dashboard</h1>
        <p className="text-sm text-slate-600">
          Top 10 most recent applications.
        </p>
        {apiHealth ? (
          <p className={`text-xs ${apiHealth.ok ? "text-emerald-700" : "text-rose-700"}`}>
            API: {apiHealth.ok ? "Connected" : "Disconnected"} ({apiHealth.apiBase}
            {apiHealth.detail ? ` — ${apiHealth.detail}` : ""})
          </p>
        ) : null}
      </header>

      {(authLoading || dataLoading) && (
        <Card>
          <p className="text-sm text-slate-600">Loading applications...</p>
        </Card>
      )}

      {globalError && (
        <Card className="border-rose-200 bg-rose-50">
          <p className="text-sm text-rose-700">{globalError}</p>
        </Card>
      )}

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {Object.entries(statusCounts).map(([status, count]) => (
          <Card key={status} className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-slate-500">{status}</p>
            <p className="text-2xl font-semibold text-slate-900">{count}</p>
          </Card>
        ))}
      </section>

      <section>
        <Card className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-600">
              <tr>
                <th className="px-2 py-2 font-medium">Company</th>
                <th className="px-2 py-2 font-medium">Role</th>
                <th className="px-2 py-2 font-medium">Link</th>
                <th className="px-2 py-2 font-medium">Status</th>
                <th className="px-2 py-2 font-medium">Date Applied</th>
                <th className="px-2 py-2 font-medium">Letter Score</th>
              </tr>
            </thead>
            <tbody>
              {mostRecentTen.map((application) => (
                <tr key={application.id} className="border-b border-slate-100">
                  <td className="px-2 py-2">{application.company}</td>
                  <td className="px-2 py-2">{application.role}</td>
                  <td className="px-2 py-2">
                    {application.jd_url ? (
                      <Link
                        href={application.jd_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-700 hover:text-slate-900"
                        aria-label="Open job link"
                      >
                        🔗
                      </Link>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-2 py-2">
                    <Badge className={statusTone[application.status]}>
                      {application.status}
                    </Badge>
                  </td>
                  <td className="px-2 py-2 text-slate-600">
                    {application.date_applied
                      ? new Date(application.date_applied).toLocaleDateString()
                      : "-"}
                  </td>
                  <td className="px-2 py-2 text-slate-600">
                    {typeof application.last_score === "number" ? `${application.last_score}%` : "-"}
                  </td>
                </tr>
              ))}
              {mostRecentTen.length === 0 && (
                <tr>
                  <td className="px-2 py-3 text-slate-500" colSpan={6}>
                    No applications found for this account yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      </section>
    </main>
  );
}
