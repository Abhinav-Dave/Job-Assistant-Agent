"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { usePhase10App } from "@/context/phase10-app-context";
import type { ApplicationStatus, JobApplication, ResumeScoreReport } from "@/types";

const PAGE_SIZE = 20;
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

export function JobsActionPanel() {
  const {
    applications,
    selectedApplicationId,
    setSelectedApplicationId,
    selectedApplication,
    executeFillInBrowserTab,
    markApplicationComplete,
    scoreResumeForApplication,
    fetchScoreReportForApplication,
    resumeFile,
    extensionTelemetry,
  } = usePhase10App();
  const [isExecutingFill, setIsExecutingFill] = useState(false);
  const [isMarkingComplete, setIsMarkingComplete] = useState(false);
  const [isScoring, setIsScoring] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [scoreResult, setScoreResult] = useState<ResumeScoreReport | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [page, setPage] = useState(1);

  const orderedApplications = useMemo(
    () => [...applications].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at)),
    [applications]
  );
  const totalPages = Math.max(1, Math.ceil(orderedApplications.length / PAGE_SIZE));
  const pagedApplications = orderedApplications.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const ensureSelectedApplication = (application: JobApplication) => {
    if (selectedApplicationId !== application.id) {
      setSelectedApplicationId(application.id);
    }
  };

  return (
    <main className="space-y-6 p-6 md:p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900">Jobs Applied</h1>
        <p className="text-sm text-slate-600">
          All applications (20 per page) with fill, complete, score, and report actions.
        </p>
      </header>

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
            {pagedApplications.map((application) => (
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
                  <Badge className={statusTone[application.status]}>{application.status}</Badge>
                </td>
                <td className="px-2 py-2 text-slate-600">
                  {application.date_applied ? new Date(application.date_applied).toLocaleDateString() : "-"}
                </td>
                <td className="px-2 py-2 text-slate-600">
                  {typeof application.last_score === "number" ? `${application.last_score}%` : "-"}
                </td>
              </tr>
            ))}
            {pagedApplications.length === 0 && (
              <tr>
                <td className="px-2 py-3 text-slate-500" colSpan={6}>
                  No applications found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div className="flex items-center justify-end gap-2 border-t border-slate-200 p-3">
          <Button
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
          >
            Prev
          </Button>
          <span className="text-xs text-slate-600">
            Page {page} / {totalPages}
          </span>
          <Button
            disabled={page >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
          >
            Next
          </Button>
        </div>
      </Card>

      {selectedApplication ? (
        <section className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
          <Card className="space-y-3">
            <h2 className="text-lg font-semibold text-slate-900">{selectedApplication.role}</h2>
            <p className="text-sm text-slate-600">{selectedApplication.company}</p>
            <p className="text-sm text-slate-600 break-all">{selectedApplication.jd_url ?? "No job URL saved"}</p>
            <Badge className="bg-slate-100 text-slate-700">{selectedApplication.status}</Badge>
            <p className="text-sm text-slate-600">{selectedApplication.notes ?? "No notes yet."}</p>
          </Card>

          <Card className="space-y-3">
            <h3 className="text-sm font-medium text-slate-700">Actions</h3>
            <Button
              className="w-full"
              disabled={isExecutingFill}
              onClick={async () => {
                ensureSelectedApplication(selectedApplication);
                const pageUrl = selectedApplication.jd_url ?? "";
                if (!pageUrl) {
                  setActionMessage("This job has no URL saved yet.");
                  return;
                }
                setIsExecutingFill(true);
                setActionMessage("Requesting extension fill for matching ATS tab...");
                const result = await executeFillInBrowserTab(pageUrl);
                setIsExecutingFill(false);
                if (!result.ok) {
                  setActionMessage(result.error || "Extension fill request failed.");
                  return;
                }
                const filled = result.telemetry
                  ? `${result.telemetry.successfulFills}/${result.telemetry.mappedFields}`
                  : "unknown";
                setActionMessage(`Extension fill executed. ${filled} fields filled.`);
              }}
            >
              {isExecutingFill ? "Executing fill..." : "Execute fill in browser tab"}
            </Button>
            <Button
              className="w-full bg-emerald-700 text-white hover:bg-emerald-600"
              disabled={isMarkingComplete}
              onClick={async () => {
                ensureSelectedApplication(selectedApplication);
                setIsMarkingComplete(true);
                const ok = await markApplicationComplete(selectedApplication.id);
                setIsMarkingComplete(false);
                setActionMessage(
                  ok ? "Job marked as submitted." : "Failed to mark job as submitted."
                );
              }}
            >
              {isMarkingComplete ? "Marking..." : "Mark as Complete"}
            </Button>
            <Button
              className="w-full bg-slate-900 text-white hover:bg-slate-700"
              disabled={isScoring || !resumeFile}
              onClick={async () => {
                ensureSelectedApplication(selectedApplication);
                setIsScoring(true);
                setActionMessage(null);
                const result = await scoreResumeForApplication(selectedApplication.id);
                setIsScoring(false);
                if (!result.ok || !result.result) {
                  setActionMessage(result.error || "Resume scoring failed.");
                  return;
                }
                const persisted = await fetchScoreReportForApplication(selectedApplication.id);
                setScoreResult(
                  persisted ?? {
                    application_id: selectedApplication.id,
                    user_id: selectedApplication.user_id,
                    ...result.result,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                  }
                );
                setActionMessage(
                  `Resume scored: ${result.result.grade} (${result.result.match_score}%).`
                );
              }}
            >
              {isScoring ? "Scoring resume..." : "Score Resume"}
            </Button>
            <Button
              className="w-full"
              disabled={isLoadingReport}
              onClick={async () => {
                ensureSelectedApplication(selectedApplication);
                setIsLoadingReport(true);
                const report = await fetchScoreReportForApplication(selectedApplication.id);
                setIsLoadingReport(false);
                if (!report) {
                  setActionMessage("No saved score report found for this job yet.");
                  return;
                }
                setScoreResult(report);
                setActionMessage("Loaded saved score report.");
              }}
            >
              {isLoadingReport ? "Loading report..." : "View Report"}
            </Button>
            {!resumeFile ? (
              <p className="text-xs text-amber-700">
                Upload a resume in the Profile tab before scoring jobs.
              </p>
            ) : null}
            {actionMessage ? <p className="text-xs text-slate-600">{actionMessage}</p> : null}
          </Card>
        </section>
      ) : (
        <Card>
          <p className="text-sm text-slate-600">No job selected from dashboard.</p>
        </Card>
      )}

      <Card className="space-y-2">
        <h3 className="text-sm font-medium text-slate-700">Latest extension telemetry</h3>
        {extensionTelemetry[0] ? (
          <p className="text-xs text-slate-500">
            {extensionTelemetry[0].successfulFills}/{extensionTelemetry[0].mappedFields} fields filled on{" "}
            {new Date(extensionTelemetry[0].completedAt).toLocaleString()}.
          </p>
        ) : (
          <p className="text-xs text-slate-500">No extension fill attempts recorded yet.</p>
        )}
      </Card>

      {scoreResult ? (
        <Card className="space-y-2">
          <h3 className="text-sm font-medium text-slate-700">Resume Score Report (Saved)</h3>
          <p className="text-sm text-slate-700">
            Grade: <span className="font-semibold">{scoreResult.grade}</span> ({scoreResult.match_score}%)
          </p>
          <p className="text-sm text-slate-600">{scoreResult.summary}</p>
          <p className="text-xs text-slate-500">
            ATS risk: {scoreResult.ats_risk} — {scoreResult.ats_risk_reason}
          </p>
        </Card>
      ) : null}
    </main>
  );
}
