# site-check

End-to-end check of `site/index.html` (v0.18): sign-in, locked cases, the pack download,
the hash check, rate limit and suspension messages, sign-out, and the Content-Security-Policy
from `vercel.json`. The edge function runs for real under Deno; Supabase Auth, the database
call and Storage are mocked in `mock.js`. The SQL is not covered here; it was checked
against PostgreSQL 16 separately when it was written.

    python3 engine/build_simulator.py
    bash engine/site-check/run.sh

Every line should start with `ok`. Console errors for blocked outside hosts (fonts, the
interview model) are ignored when the machine has no internet access.
