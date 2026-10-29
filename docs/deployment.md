# Deploying EMSim

How the live site works and how a change reaches it. Since v0.18e the normal path is a push
to GitHub. Nothing is pasted into a dashboard by hand.

Live site: https://em-case-simulator-v1.vercel.app. Supabase project: `brhtyuahzbecpnqlgxib`
(EMSim, us-west-2).

## How it works

`python3 engine/build_simulator.py` writes three things:

| Output | What it is | Where it goes |
|---|---|---|
| `build/simulator.html` | Every case inlined, no backend. For you, reviewers and the tests | Nowhere. Never deploy it |
| `site/index.html` | The engine, the case list and the sign-in form. No case content | Vercel serves `site/` |
| `private-packs/*.json` | One file per case. Not committed | The GitHub Action uploads them to the private `case-packs` bucket |

When an invited user signs in and opens a case, the site calls the `case-pack` edge
function with their session, the case name and the SHA-256 of the pack this build expects.
The function checks the account, applies the rate limit, logs the attempt, and returns
`case-packs/<PREFIX>/<sha256>.json`. The site checks the hash again before playing it.

Packs are stored by content, so every version stays in the bucket. A page built before a
change keeps loading its own packs, and a new page loads the new ones. That is why the site
and the packs can go live in either order.

**While the GitHub repository is public, this protects nothing.** `cases/`, `build/` and
the git history are readable on GitHub. The protection starts when the repository is
private.

## Making a change

1. Change the cases or the engine, then run `python3 engine/build_simulator.py`.
2. Commit everything the build changed, including `site/index.html` and `vercel.json`, and
   push to `main`.
3. Two things then happen on their own:
   - Vercel deploys `site/` (about a minute).
   - The GitHub Action "Publish case packs" builds the same commit, checks that the
     committed `site/index.html` is exactly what the build produces, and uploads any new
     packs, reading each back to check its hash. See the Actions tab on GitHub.
4. For about a minute after a push, a case that changed may say "This case is not available
   right now. If it was just updated, try again in a minute." Unchanged cases keep working.

If the Action fails with "not what the build produces", step 1 or 2 was skipped: rebuild,
commit and push again.

**Database and function changes** (new tables, a new rule in the edge function): Claude
writes them as a new numbered file in `supabase/migrations/` or an edit to
`supabase/functions/case-pack/index.ts`, and applies them through the Supabase connector in
Claude. The files in git are the record of what is live.

## What is set up, and where

| Piece | Where it lives | Who changes it |
|---|---|---|
| Tables, rate limit, bucket | `supabase/migrations/001_access.sql`, applied 29 Sep 2026 | Claude, via the connector |
| Saved progress (`public.runs`) | `supabase/migrations/002_runs.sql`, applied 28 Oct 2026 | Claude, via the connector |
| Ambulance Run leaderboard (`public.arcade_runs`) | `supabase/migrations/003_arcade.sql`, applied 29 Oct 2026 | Claude, via the connector |
| Edge function `case-pack` (Verify JWT on) | `supabase/functions/case-pack/index.ts` | Claude, via the connector |
| Allowed site address | `DEFAULT_ORIGINS` in the function. The secret `ALLOWED_ORIGINS` overrides it if set | Code change |
| Rate limits | 20 per hour, 100 per day. Secrets `CASE_LOADS_PER_HOUR` and `CASE_LOADS_PER_DAY` override them | Dashboard, Edge Functions, Secrets |
| Supabase URL and publishable key | `engine/site-config.json` (public by design) | Code change |
| PostHog project key and host | `engine/site-config.json` (public by design) | Code change |
| Pack upload | `.github/workflows/publish-packs.yml` and `engine/publish_packs.js` | Code change |
| Secret key for uploads | GitHub secret `SUPABASE_SECRET_KEY` | You only |
| Sign-ups off, Site URL | Supabase dashboard, Authentication | Dashboard |
| Users and passwords | Supabase dashboard, Authentication, Users | You only |

## One-time setup (done once per project)

1. **Secret key into GitHub.** Supabase dashboard, Project Settings, API Keys, Secret keys:
   create or reveal one and copy it (`sb_secret_...`). GitHub repository, Settings, Secrets
   and variables, Actions, New repository secret: name `SUPABASE_SECRET_KEY`, paste, save.
   Never put this key anywhere else. It bypasses every access rule in the database.
2. **Authentication settings.** Authentication, Sign In / Providers: turn off "Allow new
   users to sign up" (email and password stays on). Authentication, URL Configuration:
   Site URL `https://em-case-simulator-v1.vercel.app`.
3. **Vercel.** Project Settings, Build and Deployment: Root Directory empty, Framework
   Preset Other, no overrides. `vercel.json` sets the output folder and the headers. If
   the live page title says "(local build)", the Root Directory is wrong.
4. **First upload.** GitHub, Actions, "Publish case packs", Run workflow (or push any commit).

## Sign-up (open since v0.19)

Anyone can create an account. The welcome page's Sign up button offers Google only, because
Google hands over a verified email. For this to work, Supabase, Authentication, Sign In /
Providers, "Allow new users to sign up" must be ON.

Email and password sign-up is built but switched off (`emailSignUp` in site-config.json).
Turn it on only after setting up an email provider (Authentication, Emails, SMTP), because
Supabase's built-in email sends 2 messages an hour to team members only, so new users would
never get their confirmation link. Until they confirm, the edge function refuses them.

With sign-up open, every new account can open every case. Consider CAPTCHA
(Authentication, Attack Protection) once traffic grows.

## Google sign-in

The site offers "Continue with Google" when `googleSignIn` is true in
`engine/site-config.json`. A user who picks Google with the same email as an existing account is linked to it.

One-time setup, before turning it on:

1. Google Auth Platform (console.cloud.google.com/auth): create a project if needed, set the
   audience to External, and add the app name and a support email.
2. Clients, Create client, type **Web application**.
   - Authorized JavaScript origins: `https://em-case-simulator-v1.vercel.app`
   - Authorized redirect URIs: `https://brhtyuahzbecpnqlgxib.supabase.co/auth/v1/callback`
   Create, then copy the Client ID and Client Secret.
3. Supabase, Authentication, Sign In / Providers, Google: turn it on, paste the Client ID and
   Client Secret, save. The secret stays in Supabase only.
4. Set `googleSignIn` to true, rebuild, commit and push.

Source: [Login with Google](https://supabase.com/docs/guides/auth/social-login/auth-google),
[Identity linking](https://supabase.com/docs/guides/auth/auth-identity-linking).

## Analytics (PostHog)

The site sends product events to PostHog (US cloud) once `posthogKey` in
`engine/site-config.json` holds the project API key (`phc_...`, public by design). The
local build never loads PostHog. `engine/analytics.js` has the code, and the library is the
vendored no-external build in `engine/vendor/posthog-js/`, so recording, surveys and the
toolbar cannot be switched on from the PostHog dashboard.

Choices (29 Sep 2026): no session recording, autocapture off (it reads the text of what is
clicked, which is often case content), learners identified by Supabase user id only, never
email or name. Events never carry case text, typed questions, orders, diagnoses or notes.

| Event | Properties |
|---|---|
| `$pageview`, `$pageleave` | PostHog defaults |
| `signin_succeeded`, `signin_failed` | `reason`: wrong_credentials, network, other |
| `signed_out` | |
| `case_loaded`, `case_load_failed` | `case`, `ms`, `bytes`, or `reason` and `status` |
| `case_opened`, `case_started` | `case`, `mode` |
| `case_finished` | `case`, `mode`, `outcome` (all, missed, failed), `ended_by`, `sim_seconds`, `critical_done`, `critical_total`, `actions`, `interview_questions`, `exams`, `voice_orders`, `search_opens` |
| `debrief_revealed` | `case` |
| `run_saved` | `case`. The first save of a new run |
| `run_resumed` | `case`, `sim_seconds` |
| `run_discarded` | `case`, `reason`: start_over, version, deleted |
| `attempt_deleted` | `case` |
| `theme_changed` | `theme`: day, night |
| `run_save_failed` | `case`, `at`: finish |
| `js_error` | `message` (200 characters), `case`. At most five per page load |
| `landing_viewed` | The signed-out welcome page, once per page load |
| `landing_demo_action` | `action` (the demo's own buttons: sit, nrb, bipap, ecg, meto), `step`. Reading the demo's twelve-lead sends `action`: ecg_read, `step`: 3, `correct` (true or false) and `tries`, never the answer chosen |
| `landing_demo_end` | `outcome` (ecg, crash, tiring), `actions`, `seconds` |
| `landing_case_clicked` | `case` |
| `signup_clicked`, `login_clicked` | `from`: demo, header, page |

PostHog drops events from browsers that identify as automated, so test runs of the site
check do not appear in PostHog.

Recommended PostHog project settings: Settings, Project, turn on "Discard client IP data".

## Saved progress (28 October 2026)

A signed-in learner's runs are kept in `public.runs` (`supabase/migrations/002_runs.sql`).
The browser code is `engine/progress.js`. The local build has none of it.

- **In progress.** The run's action log, case clock, mode, open tab, the handoff being
  drafted and the six-minute pause notes, saved within 5 seconds of an action, every 15
  seconds of case time, on pause, when the leave dialog opens, and on page close (a
  keepalive request of at most 60 KB). One run in progress per learner per case.
- **Resume.** From the home panel or the case's splash. The run opens paused at the saved
  case time, with no nurse card. Start over deletes the saved run.
- **Finished.** The row keeps the outcome, how it ended, the overall score (null when the
  debrief does not score the run), the critical actions done, and the Summary rows (label,
  percentage, one line of counts). The database empties the saved log at that moment, so the
  typed questions and notes of a run are not kept after the debrief.
- **Case changed.** Each case in the site carries `versionKey`, a build-time hash of its
  pack, `engine/engine.js` and the shared catalog: everything that replaying a log reads. A
  run saved under a different key is not resumed. The splash says "This case has been
  improved" and the run is deleted (owner decision). Any change to the engine or the catalog
  therefore ends every run in progress when it is deployed.
- **Delete.** Learners can delete any run or attempt from the home panel. Deleting an account
  deletes its runs.
- **Who sees it.** Each learner sees only their own rows (row-level security, and column
  grants so the browser cannot set the owner, the case of an existing run or any timestamp).
  Programs never see progress. The scores are computed in the learner's browser, so they are
  a record for the learner, not evidence for anyone else.
- **Limits.** 256 KB of saved state per run, 50 runs in progress and 2000 rows per learner.
- **Free or paid.** Not decided. `profiles.plan` is not read.

## Adding a user

Authentication, Users, Add user, **Create new user**, enter email and a password, tick
**Auto Confirm User**. Send them the password by a private channel. A profile row is made
automatically. The function refuses unconfirmed and anonymous accounts.

Supabase's built-in email is for testing only. Its documentation says the rate is "set to
2 messages per hour" and that it "will only send messages to" members of the project
team ([source](https://supabase.com/docs/guides/auth/auth-smtp)). Set up an email provider
before relying on email.

## Check after a change

1. Open the site signed out: every case has a lock, "Invite only" above the list, title "EMSim".
2. Sign in, open a case, play a minute.
3. Browser console: no "Content Security Policy" messages.
4. Claude can confirm through the connector: a new `ok` row in `case_access`, and the
   function logs.
5. Leave the case through Main menu: the dialog says the progress is saved. The case list's
   left side shows it under Continue. Resume it, then finish it: it moves to Your attempts
   with its score. Claude can confirm a `finished` row in `public.runs` with `state` empty.

To test locally against the real project: set the secret `ALLOWED_ORIGINS` to
`https://em-case-simulator-v1.vercel.app,http://localhost:8000`, then
`python3 -m http.server 8000 --directory site`. Local servers do not send the `vercel.json`
headers, so this does not test the CSP.

Vercel's Hobby plan is for non-commercial use: "Hobby teams are restricted to non-commercial
personal use only" ([source](https://vercel.com/docs/limits/fair-use-guidelines)). Move to
Pro before Paddle goes live.

## Managing access

In the SQL Editor:

```sql
-- suspend someone (they keep their account but cannot open cases)
update public.profiles set status = 'suspended'
where user_id = (select id from auth.users where email = 'person@example.com');

-- restore
update public.profiles set status = 'active'
where user_id = (select id from auth.users where email = 'person@example.com');

-- recent case loads
select u.email, a.case_prefix, a.reason, a.created_at
from public.case_access a join auth.users u on u.id = a.user_id
order by a.created_at desc limit 50;
```

Deleting a user in Authentication, Users removes their profile and log rows too.

Every case that opens is logged. Refusals are logged at most once a minute per account,
so a script retrying a refused request cannot grow the table, and an account with no
profile row is refused without a log row.

## What each message in the site means

| The user sees | Cause |
|---|---|
| Sign-in is not configured for this build | `site-config.json` had no URL or key when `site/` was built |
| That email and password do not match an invited account | Wrong password, or no such user |
| Your account does not have access to cases right now | Profile suspended, no profile row, an anonymous account, or an email that is not confirmed |
| You have opened a lot of cases in a short time | Rate limit (step 5) |
| This case is not available right now | The pack for this build is not in the bucket yet. Normal for a minute after a push. Longer means the Action failed: check GitHub, Actions |
| This case is being updated | The pack came back with different bytes than this build expects. Should not happen with content-addressed packs; tell Claude |
| Could not reach the server | Network, the function is not deployed, or the site's address is not in the function's allowed origins (the browser reports that as a network failure) |

## Not built yet

Watermarking (planned, not a priority), password reset by email,
CAPTCHA, Paddle, PostHog and Sentry. PostHog and Sentry will each need their hosts added to
`CSP_BASE` in `engine/build_simulator.py`. Cloudflare R2 is not needed for this: Supabase
Storage holds the packs. R2 may earn a place later for large video on the marketing page,
because it does not charge for downloads.

## Ambulance Run leaderboard (29 October 2026)

The game is `engine/arcade.js`, inlined in `site/index.html` like the rest of the engine. Its
leaderboard is `public.arcade_runs` (`supabase/migrations/003_arcade.sql`). The browser has no
access to the table, only to three functions:

| Function | Who | What |
|---|---|---|
| `arcade_top()` | anyone | The top 10: name, score, time, and whether it is yours |
| `arcade_start()` | signed-in, confirmed, active profile | Starts a run. The server keeps the start time. One every 2 seconds, 300 a day |
| `arcade_finish(run, score, name)` | same | Posts a score. Refused if higher than 80 points a second since the start plus 50 (the game's top speed is 72) |

Runs never posted are deleted after 6 hours. Posted scores outside the best 100 are deleted
when a new one is posted. Names are public and are not screened. To remove one:

```sql
delete from public.arcade_runs where name = 'THE NAME';
```

Applied through the Supabase connector on 29 October 2026 and checked as a signed-in user in a
transaction that was not kept: a second start within 2 seconds, an impossible score, a bad name,
a second post of the same run and a direct read of the table are all refused. The Supabase
security advisor flags the three functions as callable. That is by design.

## Procedures (28 October 2026)

`python3 engine/build_simulator.py` also writes `private-packs/<P>.json` for each procedure
in `procedures/` and `site/px/procsim-<hash>.js`, the procedure code (three.js and
`engine/procsim-*.js`). Commit `site/px/` with `site/index.html`. The Action uploads the
procedure packs with the case packs (`engine/publish_packs.js` reads both blocks). Opening a
procedure is logged in `case_access` under its prefix and counts toward the same rate limit
as cases. Events: `procedures_opened`, `procedure_loaded`, `procedure_load_failed`
(`procedure`, `reason`), `procedure_started` (`procedure`, `mode`, `hand`),
`procedure_finished` (`procedure`, `mode`, `seconds`, `errors`, `critical`, `clean`, `total`).
