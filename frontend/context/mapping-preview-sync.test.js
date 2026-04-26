import assert from "node:assert/strict";
import test from "node:test";

import {
  getMappingPreviewWarning,
  pickSelectedApplicationId,
} from "./mapping-preview-sync.js";

test("selects tracker application id after mapping preview sync", () => {
  const applications = [
    { id: "a-1", jd_url: "https://jobs.example.com/old" },
    { id: "a-2", jd_url: "https://jobs.example.com/new-role" },
  ];
  const selected = pickSelectedApplicationId({
    currentSelectedId: "a-1",
    trackerApplicationId: "a-2",
    applications,
    pageUrl: "https://jobs.example.com/new-role",
  });
  assert.equal(selected, "a-2");
});

test("falls back to URL match to keep jobs/dashboard in sync", () => {
  const applications = [{ id: "a-9", jd_url: "https://jobs.example.com/apply?a=1&b=2" }];
  const selected = pickSelectedApplicationId({
    currentSelectedId: "",
    trackerApplicationId: null,
    applications,
    pageUrl: "https://jobs.example.com/apply?a=1&b=2",
  });
  assert.equal(selected, "a-9");
});

test("returns warning only when mapping succeeded but tracker sync failed", () => {
  assert.equal(
    getMappingPreviewWarning({
      tracker_sync: "failed",
      tracker_sync_message: "Mapping completed, but job was not added to tracker.",
    }),
    "Mapping completed, but job was not added to tracker."
  );
  assert.equal(getMappingPreviewWarning({ tracker_sync: "updated" }), null);
});
