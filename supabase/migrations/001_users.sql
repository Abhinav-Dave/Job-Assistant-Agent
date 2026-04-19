-- PRD Section 10 — users (run after Supabase Auth exists)
CREATE TABLE users (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email           TEXT UNIQUE NOT NULL,
  full_name       TEXT NOT NULL,
  phone           TEXT,
  location        TEXT,
  linkedin_url    TEXT,
  portfolio_url   TEXT,
  skills          TEXT[] DEFAULT '{}',
  preferences     JSONB DEFAULT '{}',
  onboarding_complete BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON users FOR INSERT WITH CHECK (auth.uid() = id);
