-- PRD Section 10 — education
CREATE TABLE education (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  institution     TEXT NOT NULL,
  degree          TEXT NOT NULL,
  field_of_study  TEXT,
  graduation_year INTEGER,
  gpa             DECIMAL(3,2),
  display_order   INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE education ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own education" ON education
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
