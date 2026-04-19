-- PRD Section 10 — applications
CREATE TABLE applications (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company         TEXT NOT NULL,
  role            TEXT NOT NULL,
  jd_url          TEXT,
  jd_text         TEXT,
  status          TEXT NOT NULL DEFAULT 'saved'
                  CHECK (status IN (
                    'saved', 'submitted', 'response_received',
                    'interview_requested', 'interview_completed',
                    'onsite_requested', 'offer_received',
                    'rejected', 'withdrawn'
                  )),
  notes           TEXT,
  date_applied    DATE,
  last_score      INTEGER,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own applications" ON applications
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE INDEX idx_applications_user_status ON applications(user_id, status);
CREATE INDEX idx_applications_updated ON applications(user_id, updated_at DESC);
