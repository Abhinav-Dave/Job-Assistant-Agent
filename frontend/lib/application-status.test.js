import assert from "node:assert/strict";
import test from "node:test";

import { getDisplayApplicationStatus } from "./application-status.js";

test("shows in_progress for legacy saved mapping-preview notes", () => {
  const status = getDisplayApplicationStatus({
    status: "saved",
    notes: "[mapping_preview][in_progress] Added automatically after successful mapping preview.",
  });
  assert.equal(status, "in_progress");
});

test("keeps submitted as submitted", () => {
  const status = getDisplayApplicationStatus({
    status: "submitted",
    notes: "[mapping_preview][in_progress] Added automatically after successful mapping preview.",
  });
  assert.equal(status, "submitted");
});
