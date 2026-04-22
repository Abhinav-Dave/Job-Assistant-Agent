"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { usePhase10App } from "@/context/phase10-app-context";
import type { ApplicationStatus } from "@/types";

const statusTone: Record<ApplicationStatus, string> = {
  saved: "bg-slate-100 text-slate-700",
  applied: "bg-blue-100 text-blue-700",
  interviewing: "bg-amber-100 text-amber-800",
  offer: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-700",
};

export function ApplicationTrackerDashboard() {
  const {
    applications,
    selectedApplicationId,
    setSelectedApplicationId,
    selectedApplication,
    updateApplicationNotes,
  } = usePhase10App();

  const statusCounts = applications.reduce<Record<ApplicationStatus, number>>(
    (accumulator, application) => ({
      ...accumulator,
      [application.status]: accumulator[application.status] + 1,
    }),
    {
      saved: 0,
      applied: 0,
      interviewing: 0,
      offer: 0,
      rejected: 0,
    }
  );

  return (
    <main className="space-y-6 p-6 md:p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900">Application Tracker Dashboard</h1>
        <p className="text-sm text-slate-600">
          Static Phase 10 dashboard with API-ready structure for statuses, notes, and history.
        </p>
      </header>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {Object.entries(statusCounts).map(([status, count]) => (
          <Card key={status} className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-slate-500">{status}</p>
            <p className="text-2xl font-semibold text-slate-900">{count}</p>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
        <Card className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-600">
              <tr>
                <th className="px-2 py-2 font-medium">Company</th>
                <th className="px-2 py-2 font-medium">Role</th>
                <th className="px-2 py-2 font-medium">Status</th>
                <th className="px-2 py-2 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => (
                <tr
                  key={application.id}
                  className={`cursor-pointer border-b border-slate-100 ${
                    selectedApplicationId === application.id ? "bg-slate-50" : ""
                  }`}
                  onClick={() => setSelectedApplicationId(application.id)}
                >
                  <td className="px-2 py-2">{application.company}</td>
                  <td className="px-2 py-2">{application.role}</td>
                  <td className="px-2 py-2">
                    <Badge className={statusTone[application.status]}>{application.status}</Badge>
                  </td>
                  <td className="px-2 py-2 text-slate-600">
                    {new Date(application.updated_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card className="space-y-3">
          {selectedApplication ? (
            <>
              <div className="space-y-1">
                <h2 className="text-sm font-medium text-slate-700">Activity timeline</h2>
                <p className="text-xs text-slate-500">
                  {selectedApplication.company} — {selectedApplication.role}
                </p>
              </div>
              <div className="space-y-2">
                {selectedApplication.history.map((item) => (
                  <div key={item.id} className="rounded-md border border-slate-200 p-2">
                    <div className="flex items-center justify-between">
                      <Badge className={statusTone[item.status]}>{item.status}</Badge>
                      <span className="text-xs text-slate-500">
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{item.note}</p>
                  </div>
                ))}
              </div>
              <div className="space-y-2">
                <label htmlFor="app-notes" className="text-sm font-medium text-slate-700">
                  Notes
                </label>
                <Textarea
                  id="app-notes"
                  value={selectedApplication.notes}
                  onChange={(event) =>
                    updateApplicationNotes(selectedApplication.id, event.target.value)
                  }
                />
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-600">No application selected.</p>
          )}
        </Card>
      </section>
    </main>
  );
}
