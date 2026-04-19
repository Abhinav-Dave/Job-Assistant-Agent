-- PRD Section 10 — agent_feedback
CREATE TABLE agent_feedback (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  agent_type      TEXT NOT NULL
                  CHECK (agent_type IN ('resume_scorer', 'answer_generator', 'autofill')),
  rating          INTEGER NOT NULL CHECK (rating IN (1, -1)),
  context         JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE agent_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can insert own feedback" ON agent_feedback
  FOR INSERT WITH CHECK (auth.uid() = user_id);
