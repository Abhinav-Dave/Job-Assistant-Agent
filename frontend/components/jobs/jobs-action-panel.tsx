"use client";

import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { usePhase10App } from "@/context/phase10-app-context";

export function JobsActionPanel() {
  const { selectedApplication, runMappingPreview, mappingState } = usePhase10App();

  const callout = useMemo(() => {
    if (!mappingState.hasLoaded || !mappingState.result) {
      return "Run mapping to inspect detected fields and confidence before opening extension.";
    }
    if (mappingState.result.diagnostic === "ats_page_not_ready") {
      return "ATS likely needs additional in-page steps. Use extension in authenticated tab.";
    }
    if (mappingState.result.diagnostic === "no_fields_detected") {
      return "No fields detected yet. Check if the page requires login or button progression.";
    }
    return "Mapping preview is ready. Launch extension to execute fill in-page.";
  }, [mappingState]);

  return (
    <main className="space-y-6 p-6 md:p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900">Jobs Detail & Action Panel</h1>
        <p className="text-sm text-slate-600">
          Clear split between mapping preview (backend) and live execution (extension).
        </p>
      </header>

      {selectedApplication ? (
        <section className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
          <Card className="space-y-3">
            <h2 className="text-lg font-semibold text-slate-900">{selectedApplication.role}</h2>
            <p className="text-sm text-slate-600">{selectedApplication.company}</p>
            <p className="text-sm text-slate-600 break-all">{selectedApplication.source_url}</p>
            <Badge className="bg-slate-100 text-slate-700">{selectedApplication.status}</Badge>
            <p className="text-sm text-slate-600">{selectedApplication.notes}</p>
          </Card>

          <Card className="space-y-3">
            <h3 className="text-sm font-medium text-slate-700">Actions</h3>
            <Button
              className="w-full bg-slate-900 text-white hover:bg-slate-700"
              onClick={() => runMappingPreview("success")}
            >
              Run mapping
            </Button>
            <Button className="w-full">Open extension to execute fill</Button>
            <p className="text-xs text-slate-500">{callout}</p>
          </Card>
        </section>
      ) : (
        <Card>
          <p className="text-sm text-slate-600">No job selected from dashboard.</p>
        </Card>
      )}

      <Card className="space-y-2">
        <h3 className="text-sm font-medium text-slate-700">Execution model</h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
          <li>Backend maps fields and returns confidence-scored suggestions.</li>
          <li>Extension performs live fill inside authenticated browser session.</li>
          <li>Telemetry from extension will feed this panel in Phase 11.</li>
        </ul>
      </Card>
    </main>
  );
}
