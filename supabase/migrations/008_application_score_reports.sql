-- Persist resume scoring reports by application.
CREATE TABLE IF NOT EXISTS application_score_reports (
  application_id UUID PRIMARY KEY REFERENCES applications(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  match_score INTEGER NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
  grade TEXT NOT NULL,
  summary TEXT NOT NULL,
  matched_skills TEXT[] NOT NULL DEFAULT '{}',
  missing_skills TEXT[] NOT NULL DEFAULT '{}',
  suggestions TEXT[] NOT NULL DEFAULT '{}',
  jd_key_requirements TEXT[] NOT NULL DEFAULT '{}',
  ats_risk TEXT NOT NULL,
  ats_risk_reason TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE application_score_reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "application_score_reports_select_own" ON application_score_reports;
CREATE POLICY "application_score_reports_select_own"
  ON application_score_reports
  FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "application_score_reports_insert_own" ON application_score_reports;
CREATE POLICY "application_score_reports_insert_own"
  ON application_score_reports
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "application_score_reports_update_own" ON application_score_reports;
CREATE POLICY "application_score_reports_update_own"
  ON application_score_reports
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "application_score_reports_delete_own" ON application_score_reports;
CREATE POLICY "application_score_reports_delete_own"
  ON application_score_reports
  FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_application_score_reports_user_id
  ON application_score_reports (user_id);

