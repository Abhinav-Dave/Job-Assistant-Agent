"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { usePhase10App } from "@/context/phase10-app-context";

function confidenceTone(confidence: number) {
  if (confidence >= 0.85) {
    return "bg-emerald-100 text-emerald-800";
  }
  if (confidence >= 0.5) {
    return "bg-amber-100 text-amber-800";
  }
  return "bg-rose-100 text-rose-800";
}

export function AutofillPreviewWorkspace() {
  const {
    mappingState,
    editedMappingValues,
    setEditedMappingValue,
    runMappingPreview,
  } = usePhase10App();
  const [url, setUrl] = useState("https://jobs.northstar.ai/jobs/123/apply");

  const summary = useMemo(() => {
    if (!mappingState.result) {
      return null;
    }
    const lowConfidenceCount = mappingState.result.mappings.filter(
      (mapping) => mapping.confidence < 0.85
    ).length;
    return {
      mapped: mappingState.result.mapped_fields,
      total: mappingState.result.total_fields,
      fillRatePct: Math.round(mappingState.result.fill_rate * 100),
      lowConfidenceCount,
    };
  }, [mappingState.result]);

  return (
    <main className="space-y-6 p-6 md:p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900">Autofill Mapping Preview</h1>
        <p className="text-sm text-slate-600">
          This is mapping preview only. Live execution happens in browser extension context.
        </p>
      </header>

      <Card className="space-y-3">
        <label htmlFor="job-url" className="text-sm font-medium text-slate-700">
          Job URL
        </label>
        <div className="flex flex-col gap-3 md:flex-row">
          <Input
            id="job-url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://jobs.example.com/apply"
          />
          <Button className="bg-slate-900 text-white hover:bg-slate-700" onClick={() => runMappingPreview("success")}>
            Run Mapping
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => runMappingPreview("no_fields")}>Simulate no_fields_detected</Button>
          <Button onClick={() => runMappingPreview("ats_not_ready")}>Simulate ats_page_not_ready</Button>
        </div>
      </Card>

      {mappingState.isLoading && (
        <Card>
          <p className="text-sm text-slate-600">Analyzing fields and generating mapping preview...</p>
        </Card>
      )}

      {!mappingState.isLoading && !mappingState.hasLoaded && (
        <Card>
          <p className="text-sm text-slate-600">
            No mapping has been run yet. Enter a job URL and click Run Mapping.
          </p>
        </Card>
      )}

      {mappingState.hasLoaded && mappingState.result && (
        <>
          <Card className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-slate-900 text-white">Mapped {summary?.mapped ?? 0}</Badge>
              <Badge>{summary?.fillRatePct ?? 0}% fill rate</Badge>
              <Badge className="bg-amber-100 text-amber-800">
                Low confidence: {summary?.lowConfidenceCount ?? 0}
              </Badge>
              <Badge className="bg-slate-100 text-slate-700">
                Diagnostic: {mappingState.result.diagnostic}
              </Badge>
            </div>
            {mappingState.result.diagnostic_detail && (
              <p className="text-sm text-slate-600">{mappingState.result.diagnostic_detail}</p>
            )}
          </Card>

          {mappingState.hasError && (
            <Card className="border-rose-200 bg-rose-50">
              <p className="text-sm text-rose-700">
                {mappingState.errorMessage ?? "Mapping failed unexpectedly."}
              </p>
            </Card>
          )}

          <Card className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="px-2 py-2 font-medium">Detected Field</th>
                  <th className="px-2 py-2 font-medium">Profile Key</th>
                  <th className="px-2 py-2 font-medium">Suggested Value (editable)</th>
                  <th className="px-2 py-2 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {mappingState.result.mappings.map((mapping) => (
                  <tr key={mapping.field_id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{mapping.field_label}</td>
                    <td className="px-2 py-2 text-slate-600">{mapping.profile_key}</td>
                    <td className="px-2 py-2">
                      <Input
                        value={editedMappingValues[mapping.field_id] ?? ""}
                        onChange={(event) =>
                          setEditedMappingValue(mapping.field_id, event.target.value)
                        }
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Badge className={confidenceTone(mapping.confidence)}>
                        {(mapping.confidence * 100).toFixed(0)}%
                      </Badge>
                    </td>
                  </tr>
                ))}
                {mappingState.result.mappings.length === 0 && (
                  <tr>
                    <td className="px-2 py-3 text-slate-500" colSpan={4}>
                      No editable field mappings returned.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </Card>

          <Card className="space-y-2">
            <h2 className="text-sm font-medium text-slate-700">Unfilled fields</h2>
            {mappingState.result.unfilled_fields.length > 0 ? (
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
                {mappingState.result.unfilled_fields.map((field) => (
                  <li key={field}>{field}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-600">No unfilled fields reported.</p>
            )}
          </Card>

          <Card className="border-indigo-200 bg-indigo-50">
            <p className="text-sm text-indigo-800">
              Next step: open the extension to execute fill in the authenticated browser tab.
            </p>
          </Card>
        </>
      )}
    </main>
  );
}
