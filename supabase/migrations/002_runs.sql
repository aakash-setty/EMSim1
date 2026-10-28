-- EMSim: saved progress (28 October 2026).
--
-- Applied through the Supabase connector as migration 002_runs, after 001_access. It is safe
-- to run again: every statement checks for what already exists or replaces itself.
--
-- What it creates:
--   public.runs     one row per attempt at a case, owned by the signed-in user.
--                   status 'in_progress': the run can be resumed. `state` holds what the
--                   browser needs to rebuild it (the action log, the case clock, the mode and
--                   a few screen settings).
--                   status 'finished': the score summary only. `state` is emptied when the
--                   run finishes, so the action log and anything typed into the case is not
--                   kept after the debrief.
--   public.runs_guard()   the trigger that keeps the rules below whatever the browser sends.
--
-- Owner decisions (28 October 2026):
--   - a run saved against an older version of the case is not resumed. The browser tells the
--     learner the case has been improved and deletes the run. `version_key` is what it compares.
--   - history is score summaries, not a replayable debrief.
--   - abandoned runs are discarded: starting over deletes the in-progress run. There is no
--     'abandoned' status.
--   - learners may delete their own history.
--   - free or paid: not decided. profiles.plan is not read here.
--
-- Row-level security: a signed-in user can read, add, change and delete their own rows and
-- nobody else's. Programs never see progress (owner decision, 28 September 2026); nothing
-- here grants any other role access. The scores in a row are computed by the learner's own
-- browser, so they are a record for the learner and not evidence for anyone else.

create table if not exists public.runs (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null default auth.uid() references auth.users (id) on delete cascade,
  case_prefix  text not null check (case_prefix ~ '^[A-Z][A-Z0-9]{1,15}$'),
  -- Build-time hash of the case pack, the engine and the shared catalog the run was played
  -- with. A different key means the run would not replay the same way.
  version_key  text not null check (version_key ~ '^[0-9a-f]{16,64}$'),
  mode         text not null check (char_length(mode) between 1 and 32),
  status       text not null default 'in_progress' check (status in ('in_progress', 'finished')),
  state        jsonb,
  sim_seconds  integer not null default 0 check (sim_seconds between 0 and 86400),
  outcome      text check (outcome in ('all', 'missed', 'failed')),
  ended_by     text check (ended_by in ('completed', 'clock', 'action', 'harmful_action', 'early_exit')),
  score_pct    smallint check (score_pct between 0 and 100),
  summary      jsonb,
  started_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  finished_at  timestamptz,
  constraint runs_state_size   check (state is null or octet_length(state::text) <= 262144),
  constraint runs_summary_size check (summary is null or octet_length(summary::text) <= 8192),
  constraint runs_shape check (
    (status = 'in_progress' and state is not null and finished_at is null
       and outcome is null and ended_by is null and score_pct is null and summary is null)
    or
    (status = 'finished' and state is null and finished_at is not null
       and outcome is not null and ended_by is not null)
  )
);

-- One run in progress per learner per case. A second one is refused (23505); the browser
-- deletes the older one first when the learner starts over.
create unique index if not exists runs_one_open on public.runs (user_id, case_prefix)
  where status = 'in_progress';
create index if not exists runs_user_updated on public.runs (user_id, updated_at desc);

alter table public.runs enable row level security;

revoke all on table public.runs from anon, authenticated;
grant select, delete on table public.runs to authenticated;
-- Column grants: the browser cannot set the owner, the id or any timestamp.
grant insert (case_prefix, version_key, mode, status, state, sim_seconds,
              outcome, ended_by, score_pct, summary) on table public.runs to authenticated;
grant update (mode, status, state, sim_seconds,
              outcome, ended_by, score_pct, summary) on table public.runs to authenticated;

drop policy if exists "runs: read own" on public.runs;
create policy "runs: read own" on public.runs
  for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "runs: add own" on public.runs;
create policy "runs: add own" on public.runs
  for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "runs: change own" on public.runs;
create policy "runs: change own" on public.runs
  for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "runs: delete own" on public.runs;
create policy "runs: delete own" on public.runs
  for delete to authenticated
  using ((select auth.uid()) = user_id);

-- The rules the browser cannot be trusted to keep.
--   - the server sets every timestamp.
--   - a finished run cannot be changed, only deleted.
--   - finishing a run empties `state`.
--   - id, owner, case and version never change after the row is made.
--   - at most 2000 rows and 50 runs in progress per learner, so a script cannot fill the
--     table. Counted under the learner's own row-level security, which is their own rows.
create or replace function public.runs_guard()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_total integer;
  v_open  integer;
begin
  if tg_op = 'INSERT' then
    select count(*), count(*) filter (where status = 'in_progress')
      into v_total, v_open
      from public.runs where user_id = new.user_id;
    if v_total >= 2000 then
      raise exception 'run history is full' using errcode = 'P0001', hint = 'delete older attempts';
    end if;
    if new.status = 'in_progress' and v_open >= 50 then
      raise exception 'too many runs in progress' using errcode = 'P0001';
    end if;
    new.started_at := now();
  else
    if old.status = 'finished' then
      raise exception 'a finished run cannot be changed' using errcode = 'P0001';
    end if;
    new.id          := old.id;
    new.user_id     := old.user_id;
    new.case_prefix := old.case_prefix;
    new.version_key := old.version_key;
    new.started_at  := old.started_at;
  end if;
  new.updated_at := now();
  if new.status = 'finished' then
    new.state := null;
    new.finished_at := now();
  else
    new.finished_at := null;
  end if;
  return new;
end;
$$;
revoke all on function public.runs_guard() from public, anon, authenticated;

drop trigger if exists runs_guard on public.runs;
create trigger runs_guard
  before insert or update on public.runs
  for each row execute function public.runs_guard();
