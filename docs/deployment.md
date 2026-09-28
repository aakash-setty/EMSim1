# Deploying EMSim (v0.18)

How the deployed site works, and every step to set it up. You paste things into the
Supabase dashboard and click through Vercel; nothing here needs a terminal except the
build, which you already run.

Dashboard menu names below are as of September 2026 and may move. If a label differs,
look for the nearest match.

## How it works

`python3 engine/build_simulator.py` now writes three things:

| Output | What it is | Where it goes |
|---|---|---|
| `build/simulator.html` | Every case inlined, no backend. For you, reviewers and the tests | Nowhere. Never deploy it |
| `site/index.html` | The engine, the case list and the sign-in form. No case content | Vercel serves the `site/` folder |
| `private-packs/*.json` | One file per case | Uploaded by hand to the private `case-packs` bucket in Supabase |

When an invited user signs in and opens a case, the site calls the `case-pack` edge
function with their session. The function checks the account is active, applies the rate
limit, logs the attempt, and returns the pack. The site checks the pack's SHA-256 against
the value built into `site/index.html` before playing it, so a stale or altered pack is
refused with "This case is being updated".

**While the GitHub repository is public, this protects nothing.** `cases/`, `build/` and
the git history are readable on GitHub. The protection starts when the repository is
private. Copies already cloned stay out there.

## 1. Create the Supabase project

1. Create the project. Pick the region nearest most users.
2. Settings, API Keys: copy the **Project URL** and the **publishable key** (or the legacy
   `anon` key). Both are public values that end up in the site. Send them to Claude or put
   them in `engine/site-config.json` as `supabaseUrl` and `supabaseKey`, then rebuild.
   Done in v0.18d for the project `brhtyuahzbecpnqlgxib`. The build refuses a secret or
   service_role key, so pasting the wrong one stops the build instead of publishing it.
   The "Connect" dialog in the dashboard shows Next.js steps (`npm install`, `.env.local`).
   They do not apply here: the site is one static page with supabase-js already inside it.
3. Never copy the **secret** or **service_role** key anywhere outside the dashboard. The
   edge function reads it from its own environment.

## 2. Authentication settings

1. Authentication, Sign In / Providers: turn **off** "Allow new users to sign up". Email
   and password stays on. This is what makes it invite-only.
2. Authentication, URL Configuration: set **Site URL** to the Vercel address once you have
   it.
3. Add each person: Authentication, Users, Add user, **Create new user**, enter email and
   a password, tick **Auto Confirm User**. Send them the password by a private channel.
   A profile row is made for them automatically. Since v0.18a the edge function refuses any
   account whose email is not confirmed, and any anonymous account, so a user added without
   Auto Confirm cannot open cases until they confirm.

Supabase's built-in email is for testing only. Its documentation says the rate is "set to
2 messages per hour" and that it "will only send messages to" members of the project
team ([source](https://supabase.com/docs/guides/auth/auth-smtp)). That is why this setup
creates users with a password instead of sending invitations, and why the sign-in form
says to ask the inviter for a forgotten password. Set up an email provider before you
rely on email.

## 3. Run the SQL

SQL Editor, New query, paste all of `supabase/migrations/001_access.sql`, Run. It is safe to
run again. It creates:

- `profiles`: one row per user, `status` active or suspended, `plan` free for now.
- `case_access`: one row per attempt to open a case, with the result.
- `claim_case_load`: the rate limit and the log in one step. Only the edge function can call it.
- the private storage bucket `case-packs`.

Check: Table Editor shows `profiles` and `case_access`, both with RLS enabled. Storage shows
`case-packs` marked private.

## 4. Upload the case packs

Storage, `case-packs`, Upload, select every file in `private-packs/`. When a file already
exists, choose to overwrite it.

Re-upload all of them after any rebuild that changed a case or the engine. Upload the packs
**before** pushing the new site. If the order is reversed, users see "This case is being
updated" until the packs catch up, which is safe but confusing. A rebuild that changed
nothing produces identical files.

## 5. Deploy the edge function

1. Edge Functions, Deploy a new function, Via Editor. Name it exactly `case-pack`.
2. Replace the example code with all of `supabase/functions/case-pack/index.ts`. Deploy.
3. Leave **Verify JWT** on.
4. Edge Functions, Secrets, add:

| Name | Value | Required |
|---|---|---|
| `ALLOWED_ORIGINS` | Your site address, for example `https://emsim.vercel.app`. Comma-separate several. Add `http://localhost:8000` to test locally | Yes. With none set, every request is refused |
| `CASE_LOADS_PER_HOUR` | 20 | No, 20 is the default |
| `CASE_LOADS_PER_DAY` | 100 | No, 100 is the default |

The function finds `SUPABASE_URL` and the secret key on its own.

## 6. Deploy the site on Vercel

1. Rebuild after step 1 so `site/index.html` carries the URL and key, and commit `site/`
   and `vercel.json`. `private-packs/` is ignored by git on purpose.
2. Vercel, Add New, Project, import the GitHub repository. Framework preset: Other. Leave
   the build and output settings alone: `vercel.json` says to serve `site/` with no build.
3. Deploy. Put the address it gives you into `ALLOWED_ORIGINS` (step 5) and Site URL (step 2).

`vercel.json` also sets the security headers, including a Content-Security-Policy that lists
the hash of each inline script. The build regenerates it, so always commit the two
together.

Vercel's Hobby plan is for non-commercial use: "Hobby teams are restricted to non-commercial
personal use only", and taking payment counts as commercial
([source](https://vercel.com/docs/limits/fair-use-guidelines)). Move to Pro before Paddle
goes live.

## 7. Check it

1. Open the site signed out: four cases with a lock, "Invite only" above the list.
2. Sign in with a test user, open a case, play a minute of it.
3. Open the browser console. There should be no "Content Security Policy" messages. The
   interview model loads from jsDelivr and Hugging Face; this was not testable before
   deployment, so if the console shows it blocked, tell Claude.
4. Table Editor, `case_access`: one `ok` row for the case you opened.

To test locally against the real project: add `http://localhost:8000` to `ALLOWED_ORIGINS`,
then `python3 -m http.server 8000 --directory site`. Local servers do not send the
`vercel.json` headers, so this does not test the CSP.

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
| This case is not available right now | The pack is missing from the bucket |
| This case is being updated | The pack in the bucket is not the one this site was built with. Re-upload `private-packs/` |
| Could not reach the server | Network, the function is not deployed, or the site's address is missing from `ALLOWED_ORIGINS` (the browser reports that as a network failure) |

## Not built yet

Watermarking (planned, not a priority), run history and progress, password reset by email,
CAPTCHA, Paddle, PostHog and Sentry. PostHog and Sentry will each need their hosts added to
`CSP_BASE` in `engine/build_simulator.py`. Cloudflare R2 is not needed for this: Supabase
Storage holds the packs. R2 may earn a place later for large video on the marketing page,
because it does not charge for downloads.
