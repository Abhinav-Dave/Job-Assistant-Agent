function normalizeUrl(value) {
  return String(value || "").trim().toLowerCase();
}

/**
 * Derive a stable selected application id after preview-triggered tracker sync.
 */
export function pickSelectedApplicationId({
  currentSelectedId,
  trackerApplicationId,
  applications,
  pageUrl,
}) {
  if (
    trackerApplicationId &&
    applications.some((application) => application.id === trackerApplicationId)
  ) {
    return trackerApplicationId;
  }
  if (currentSelectedId && applications.some((application) => application.id === currentSelectedId)) {
    return currentSelectedId;
  }
  const mappedMatch = applications.find(
    (application) =>
      application.jd_url && normalizeUrl(application.jd_url) === normalizeUrl(pageUrl)
  );
  return mappedMatch?.id || applications[0]?.id || "";
}

/**
 * Return non-blocking warning text only when tracker sync failed.
 */
export function getMappingPreviewWarning(backendResult) {
  if (backendResult?.tracker_sync !== "failed") {
    return null;
  }
  return (
    backendResult.tracker_sync_message ||
    "Mapping completed, but job was not added to tracker."
  );
}
