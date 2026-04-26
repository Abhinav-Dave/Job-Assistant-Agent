/**
 * @param {{ status: string; notes: string | null | undefined }} application
 */
export function getDisplayApplicationStatus(application) {
  const notes = String(application.notes || "").toLowerCase();
  if (application.status === "saved" && notes.includes("[mapping_preview][in_progress]")) {
    return "in_progress";
  }
  return application.status;
}
