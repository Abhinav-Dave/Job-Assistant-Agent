# Supabase SQL (PRD Section 10)

Run migrations **in order** in the Supabase SQL Editor, or use the Supabase CLI linked to your project.

- Private Storage bucket `resumes` must be created in the Supabase Dashboard (PRD Section 10). File path convention: `{user_id}/resume_{timestamp}.pdf`.

- `auth.users` must exist (Supabase Auth) before `001_users.sql` because of the foreign key to `auth.users(id)`.
