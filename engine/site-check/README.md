# site-check

End-to-end check of `site/index.html` (v0.18): sign-in, locked cases, the pack download,
the hash check, rate limit and suspension messages, sign-out, and the Content-Security-Policy
from `vercel.json`. `progress.js` (28 October 2026) checks saved progress against the mock's
`public.runs`: autosave, leave and resume to the same state, finishing into a score
summary, delete, Start over, the case-has-changed notice, a reload, a failing save and
phone width. The SQL rules themselves are checked separately against PostgreSQL 16
(`Claude outputs/progress/runs-sql-tests.sh`). The edge function runs for real under Deno; Supabase Auth, the database
call and Storage are mocked in `mock.js`. The SQL is not covered here; it was checked
against PostgreSQL 16 separately when it was written.

    python3 engine/build_simulator.py
    bash engine/site-check/run.sh

It also serves the site three ways: pointed at the mock, with no Supabase settings, and
exactly as built. The as-built copy is only loaded, never signed in, and any request to a
real `supabase.co` host is blocked, so the check never touches the live project.

Every line should start with `ok`. Console errors for blocked outside hosts (fonts, the
interview model) are ignored when the machine has no internet access.
