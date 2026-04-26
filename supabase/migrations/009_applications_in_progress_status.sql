-- Phase 12 P0 hotfix: allow in-progress application state.
DO $$
BEGIN
  ALTER TABLE applications
    DROP CONSTRAINT IF EXISTS applications_status_check;

  ALTER TABLE applications
    ADD CONSTRAINT applications_status_check
    CHECK (status IN (
      'saved',
      'in_progress',
      'submitted',
      'response_received',
      'interview_requested',
      'interview_completed',
      'onsite_requested',
      'offer_received',
      'rejected',
      'withdrawn'
    ));
END $$;
