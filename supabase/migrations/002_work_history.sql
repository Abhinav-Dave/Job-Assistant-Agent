-- PRD Section 10 — work_history
CREATE TABLE work_history (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company         TEXT NOT NULL,
  role            TEXT NOT NULL,
  start_date      TEXT NOT NULL,
  end_date        TEXT,
  is_current      BOOLEAN DEFAULT FALSE,
  bullets         TEXT[] DEFAULT '{}',
  display_order   INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE work_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own work history" ON work_history
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
