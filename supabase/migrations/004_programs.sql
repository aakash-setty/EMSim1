-- EMSim: programs, program members, case entitlements, run records and analytics
-- (10 November 2026).
--
-- Applied through the Supabase connector as migration 004_programs, after 003_arcade. It is
-- safe to run again: every statement checks for what already exists or replaces itself.
--
-- Owner decisions (10 November 2026), which replace the 28 September 2026 rule that
-- programs never see progress:
--   - a residency program buys seats. Its residents register under it with a join code and
--     get the cases the program paid for.
--   - individual accounts continue beside programs. A run finished before an account joined
--     a program is not part of the program's data.
--   - a program's admins see their own program's data and nobody else's. WeSim staff see
--     every program and every account, for now.
--   - a program admin always sees who has completed what, by name. Whether they also see
--     each resident's results by name is one switch per program (show_named_results),
--     which staff set. It is on for now. Off, results are shown for the group only.
--   - a member of a program cannot delete a finished run, for now.
--
-- What it creates:
--   public.app_settings     one row. enforce_entitlements is OFF, so every confirmed account
--                           can still open every case, exactly as before this file.
--   public.staff            WeSim staff accounts. Rows are added by hand through the connector.
--   public.programs         one row per program, with its join code and its switches.
--   public.program_cases    the cases a program bought, when it did not buy all of them.
--   public.program_members  one row per account that joined a program. One program per account.
--   public.run_records      one row per finished run: the three-word result, the reasons,
--                           the attempt number, the program and year at the time, the phases
--                           reached and the trail of action ids and case times.
--   public.run_items        one row per graded item of a finished run.
--
-- None of these tables can be read or written from the browser. Everything goes through
-- the functions below, each of which checks who is calling.
--
-- What a run record is worth: the browser computes it (engine/engine.js, runItems) and the
-- server stores it. The server checks its shape, its size and that it agrees with the run's
-- outcome. It does not recompute it, so `verified` is false on every row. A learner who
-- alters their own page can alter their own record. Treat the data as formative.

-- ---------------------------------------------------------------- settings and staff
create table if not exists public.app_settings (
  id                   boolean primary key default true check (id),
  enforce_entitlements boolean not null default false,
  free_cases           text[]  not null default '{}'
);
insert into public.app_settings (id) values (true) on conflict (id) do nothing;
alter table public.app_settings enable row level security;
revoke all on table public.app_settings from anon, authenticated;

create table if not exists public.staff (
  user_id  uuid primary key references auth.users (id) on delete cascade,
  added_at timestamptz not null default now()
);
alter table public.staff enable row level security;
revoke all on table public.staff from anon, authenticated;

-- ---------------------------------------------------------------- programs
create table if not exists public.programs (
  id                 uuid primary key default gen_random_uuid(),
  name               text not null check (char_length(name) between 2 and 120),
  join_code          text not null unique check (join_code ~ '^[A-HJ-NP-Z2-9]{8}$'),
  status             text not null default 'active' check (status in ('active', 'closed')),
  show_named_results boolean not null default true,
  all_cases          boolean not null default true,
  seats              integer check (seats is null or seats > 0),
  created_at         timestamptz not null default now()
);
alter table public.programs enable row level security;
revoke all on table public.programs from anon, authenticated;

create table if not exists public.program_cases (
  program_id  uuid not null references public.programs (id) on delete cascade,
  case_prefix text not null check (case_prefix ~ '^[A-Z][A-Z0-9]{1,15}$'),
  primary key (program_id, case_prefix)
);
alter table public.program_cases enable row level security;
revoke all on table public.program_cases from anon, authenticated;

create table if not exists public.program_members (
  user_id      uuid primary key references auth.users (id) on delete cascade,
  program_id   uuid not null references public.programs (id) on delete cascade,
  role         text not null default 'resident' check (role in ('resident', 'admin')),
  display_name text not null check (char_length(display_name) between 1 and 80),
  -- Postgraduate year. 0 is a medical student. Null is not said.
  pgy          smallint check (pgy between 0 and 8),
  joined_at    timestamptz not null default now()
);
create index if not exists program_members_program on public.program_members (program_id);
alter table public.program_members enable row level security;
revoke all on table public.program_members from anon, authenticated;

-- ---------------------------------------------------------------- run records
create table if not exists public.run_records (
  run_id      uuid primary key references public.runs (id) on delete cascade,
  user_id     uuid not null references auth.users (id) on delete cascade,
  program_id  uuid references public.programs (id) on delete set null,
  pgy         smallint,
  case_prefix text not null,
  attempt_no  integer not null check (attempt_no >= 1),
  result      text not null check (result in ('met', 'met_prompted', 'not_met')),
  why         text[] not null default '{}',
  counts      jsonb,
  phases      jsonb,
  trail       jsonb,
  verified    boolean not null default false,
  created_at  timestamptz not null default now()
);
create index if not exists run_records_program on public.run_records (program_id, case_prefix);
create index if not exists run_records_user on public.run_records (user_id, case_prefix);
alter table public.run_records enable row level security;
revoke all on table public.run_records from anon, authenticated;

create table if not exists public.run_items (
  run_id     uuid not null references public.run_records (run_id) on delete cascade,
  idx        smallint not null,
  kind       text not null check (kind in ('critical', 'recommended', 'discouraged', 'harmful', 'diagnosis', 'disposition')),
  item_id    text,
  tab        text,
  cat        text,
  grp        text,
  result     text not null check (result in ('done', 'missed', 'taken', 'correct', 'defensible', 'incorrect', 'none')),
  prompted   boolean not null default false,
  expected_t numeric(9,3),
  done_t     numeric(9,3),
  primary key (run_id, idx)
);
create index if not exists run_items_item on public.run_items (kind, item_id);
alter table public.run_items enable row level security;
revoke all on table public.run_items from anon, authenticated;

-- ---------------------------------------------------------------- who is calling
create or replace function public.is_staff()
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.staff s where s.user_id = (select auth.uid()));
$$;

create or replace function public.is_program_member()
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.program_members m where m.user_id = (select auth.uid()));
$$;

revoke all on function public.is_staff() from public, anon;
revoke all on function public.is_program_member() from public, anon;
grant execute on function public.is_staff() to authenticated;
grant execute on function public.is_program_member() to authenticated;

-- A member of a program cannot delete a finished run (owner decision, 10 November 2026).
-- A run in progress can still be discarded, which is how Start over works.
drop policy if exists "runs: delete own" on public.runs;
create policy "runs: delete own" on public.runs
  for delete to authenticated
  using ((select auth.uid()) = user_id
         and (status = 'in_progress' or not (select public.is_program_member())));

-- ---------------------------------------------------------------- entitlements
-- True when the account may open the case. Read only when enforce_entitlements is on.
create or replace function public.case_entitled(p_user uuid, p_prefix text)
returns boolean language sql stable security definer set search_path = '' as $$
  select
    exists (select 1 from public.app_settings s where p_prefix = any (s.free_cases))
    or exists (select 1 from public.staff s where s.user_id = p_user)
    or exists (select 1 from public.profiles p where p.user_id = p_user and p.plan = 'paid')
    or exists (select 1 from public.program_members m
                 join public.programs g on g.id = m.program_id
                where m.user_id = p_user and g.status = 'active'
                  and (g.all_cases or exists (select 1 from public.program_cases c
                                               where c.program_id = g.id and c.case_prefix = p_prefix)));
$$;
revoke all on function public.case_entitled(uuid, text) from public, anon, authenticated;

-- claim_case_load, as in 001_access.sql, with one more answer: 'not_entitled'. It is given
-- only when app_settings.enforce_entitlements is on, which it is not.
create or replace function public.claim_case_load(
  p_user uuid, p_prefix text, p_per_hour integer, p_per_day integer)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_status  text;
  v_hour    integer;
  v_day     integer;
  v_result  text;
  v_enforce boolean;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_user::text, 0));

  select status into v_status from public.profiles where user_id = p_user;
  select enforce_entitlements into v_enforce from public.app_settings where id;

  if v_status is null then
    v_result := 'no_profile';
  elsif v_status <> 'active' then
    v_result := 'suspended';
  elsif coalesce(v_enforce, false) and not public.case_entitled(p_user, p_prefix) then
    v_result := 'not_entitled';
  else
    select count(*) filter (where created_at > now() - interval '1 hour'),
           count(*)
      into v_hour, v_day
      from public.case_access
     where user_id = p_user and allowed and created_at > now() - interval '1 day';
    if v_hour >= p_per_hour or v_day >= p_per_day then
      v_result := 'rate_limited';
    else
      v_result := 'ok';
    end if;
  end if;

  if v_result = 'ok' or (v_result <> 'no_profile' and not exists (
       select 1 from public.case_access
        where user_id = p_user and not allowed and created_at > now() - interval '1 minute')) then
    insert into public.case_access (user_id, case_prefix, allowed, reason)
    values (p_user, left(p_prefix, 32), v_result = 'ok', v_result);
  end if;
  return v_result;
end;
$$;
revoke all on function public.claim_case_load(uuid, text, integer, integer) from public, anon, authenticated;
grant execute on function public.claim_case_load(uuid, text, integer, integer) to service_role;

-- ---------------------------------------------------------------- my_program
-- What the signed-in account is: staff or not, and its program if it has one.
create or replace function public.my_program()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  v_uid uuid := (select auth.uid());
  v_out jsonb;
begin
  if v_uid is null then raise exception 'sign in first' using errcode = '42501'; end if;
  select jsonb_build_object(
           'staff', exists (select 1 from public.staff s where s.user_id = v_uid),
           'enforce', (select enforce_entitlements from public.app_settings where id),
           'free_cases', (select to_jsonb(free_cases) from public.app_settings where id),
           'member', (
             select jsonb_build_object(
                      'program_id', g.id, 'program', g.name, 'status', g.status,
                      'role', m.role, 'display_name', m.display_name, 'pgy', m.pgy,
                      'show_named_results', g.show_named_results, 'all_cases', g.all_cases,
                      'cases', coalesce((select jsonb_agg(c.case_prefix order by c.case_prefix)
                                           from public.program_cases c where c.program_id = g.id), '[]'::jsonb),
                      'join_code', case when m.role = 'admin' then g.join_code end)
               from public.program_members m join public.programs g on g.id = m.program_id
              where m.user_id = v_uid))
    into v_out;
  return v_out;
end;
$$;

-- ---------------------------------------------------------------- join_program
-- Returns 'ok', 'bad_code', 'closed', 'full', 'already_member' or 'bad_name'.
create or replace function public.join_program(p_code text, p_name text, p_pgy integer)
returns text language plpgsql security definer set search_path = '' as $$
declare
  v_uid  uuid := (select auth.uid());
  v_prog public.programs%rowtype;
  v_name text := btrim(regexp_replace(coalesce(p_name, ''), '\s+', ' ', 'g'));
  v_n    integer;
begin
  if v_uid is null then raise exception 'sign in first' using errcode = '42501'; end if;
  if exists (select 1 from public.program_members where user_id = v_uid) then return 'already_member'; end if;
  if char_length(v_name) < 1 or char_length(v_name) > 80 then return 'bad_name'; end if;
  select * into v_prog from public.programs
   where join_code = upper(regexp_replace(coalesce(p_code, ''), '[^A-Za-z0-9]', '', 'g'));
  if not found then
    -- A wrong code costs a second, so codes cannot be tried quickly.
    perform pg_sleep(1);
    return 'bad_code';
  end if;
  if v_prog.status <> 'active' then return 'closed'; end if;
  perform pg_advisory_xact_lock(hashtextextended(v_prog.id::text, 0));
  if v_prog.seats is not null then
    select count(*) into v_n from public.program_members where program_id = v_prog.id and role = 'resident';
    if v_n >= v_prog.seats then return 'full'; end if;
  end if;
  insert into public.program_members (user_id, program_id, display_name, pgy)
  values (v_uid, v_prog.id, v_name, case when p_pgy between 0 and 8 then p_pgy end);
  return 'ok';
end;
$$;

-- ---------------------------------------------------------------- record_run
-- Stores the record of one of the caller's finished runs. Returns 'ok', 'no_run', 'exists',
-- 'bad_record' or 'mismatch'. The record is engine/engine.js runItems(); the trail is the
-- action log with everything typed left out.
create or replace function public.record_run(p_run uuid, p_record jsonb, p_trail jsonb)
returns text language plpgsql security definer set search_path = '' as $$
declare
  v_uid     uuid := (select auth.uid());
  v_run     public.runs%rowtype;
  v_result  text;
  v_attempt integer;
  v_prog    uuid;
  v_pgy     smallint;
  v_trail   jsonb := p_trail;
begin
  if v_uid is null then raise exception 'sign in first' using errcode = '42501'; end if;
  select * into v_run from public.runs where id = p_run and user_id = v_uid and status = 'finished';
  if not found then return 'no_run'; end if;
  if exists (select 1 from public.run_records where run_id = p_run) then return 'exists'; end if;

  if p_record is null or jsonb_typeof(p_record) <> 'object'
     or jsonb_typeof(p_record -> 'items') is distinct from 'array'
     or jsonb_array_length(p_record -> 'items') > 400
     or octet_length(p_record::text) > 131072 then
    return 'bad_record';
  end if;
  v_result := p_record ->> 'result';
  if v_result is null or v_result not in ('met', 'met_prompted', 'not_met') then return 'bad_record'; end if;
  -- The one cross-check the server can make: a run that missed a critical action or was
  -- lost cannot claim to have met the case.
  if v_result <> 'not_met' and v_run.outcome <> 'all' then return 'mismatch'; end if;
  if v_trail is not null and (jsonb_typeof(v_trail) <> 'array' or octet_length(v_trail::text) > 262144) then
    v_trail := null;
  end if;

  select 1 + count(*) into v_attempt from public.runs
   where user_id = v_uid and case_prefix = v_run.case_prefix and status = 'finished'
     and id <> v_run.id and finished_at <= v_run.finished_at;
  select m.program_id, m.pgy into v_prog, v_pgy from public.program_members m where m.user_id = v_uid;

  insert into public.run_records (run_id, user_id, program_id, pgy, case_prefix, attempt_no,
                                  result, why, counts, phases, trail)
  values (p_run, v_uid, v_prog, v_pgy, v_run.case_prefix, v_attempt, v_result,
          coalesce((select array_agg(left(x, 32)) from jsonb_array_elements_text(
                      case when jsonb_typeof(p_record -> 'why') = 'array' then p_record -> 'why' else '[]'::jsonb end) x), '{}'),
          case when jsonb_typeof(p_record -> 'counts') = 'object' then p_record -> 'counts' end,
          case when jsonb_typeof(p_record -> 'phases') = 'array' then p_record -> 'phases' end,
          v_trail);

  insert into public.run_items (run_id, idx, kind, item_id, tab, cat, grp, result, prompted, expected_t, done_t)
  select p_run, (o.n - 1)::smallint, o.i ->> 'k', left(o.i ->> 'id', 96), left(o.i ->> 'tab', 32),
         left(o.i ->> 'cat', 32), left(o.i ->> 'grp', 64), o.i ->> 'r',
         coalesce(o.i ->> 'p', 'false') = 'true',
         case when jsonb_typeof(o.i -> 'et') = 'number' and (o.i ->> 'et')::numeric between 0 and 86400 then round((o.i ->> 'et')::numeric, 3) end,
         case when jsonb_typeof(o.i -> 'dt') = 'number' and (o.i ->> 'dt')::numeric between 0 and 86400 then round((o.i ->> 'dt')::numeric, 3) end
    from jsonb_array_elements(p_record -> 'items') with ordinality as o(i, n)
   where jsonb_typeof(o.i) = 'object'
     and o.i ->> 'k' in ('critical', 'recommended', 'discouraged', 'harmful', 'diagnosis', 'disposition')
     and o.i ->> 'r' in ('done', 'missed', 'taken', 'correct', 'defensible', 'incorrect', 'none');
  return 'ok';
end;
$$;

-- ---------------------------------------------------------------- program_analytics
-- One program's data for its admins, or any program's for staff. p_program null is every
-- account, staff only. p_first true counts first attempts only. p_days limits to runs
-- finished in the last p_days days.
create or replace function public.program_analytics(
  p_program uuid default null, p_first boolean default true, p_days integer default null)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  v_uid   uuid := (select auth.uid());
  v_staff boolean;
  v_prog  public.programs%rowtype;
  v_named boolean;
  v_out   jsonb;
begin
  if v_uid is null then raise exception 'sign in first' using errcode = '42501'; end if;
  v_staff := exists (select 1 from public.staff s where s.user_id = v_uid);
  if p_program is null then
    if not v_staff then raise exception 'not allowed' using errcode = '42501'; end if;
    v_named := true;
  else
    if not v_staff and not exists (select 1 from public.program_members m
                                    where m.user_id = v_uid and m.program_id = p_program and m.role = 'admin') then
      raise exception 'not allowed' using errcode = '42501';
    end if;
    select * into v_prog from public.programs where id = p_program;
    if not found then raise exception 'no such program' using errcode = 'P0002'; end if;
    v_named := v_staff or v_prog.show_named_results;
  end if;

  with rec as (
    select r.run_id, r.user_id, r.pgy, r.case_prefix, r.attempt_no, r.result, r.why,
           u.sim_seconds, u.finished_at
      from public.run_records r join public.runs u on u.id = r.run_id
     where (p_program is null or r.program_id = p_program)
       and (p_days is null or u.finished_at > now() - make_interval(days => p_days))
  ),
  sel as (select * from rec where not p_first or attempt_no = 1),
  people as (
    select m.user_id, m.display_name, m.pgy, m.role, m.joined_at
      from public.program_members m where p_program is not null and m.program_id = p_program
    union all
    select x.user_id, m.display_name, m.pgy, coalesce(m.role, 'individual'), m.joined_at
      from (select distinct user_id from rec) x
      left join public.program_members m on m.user_id = x.user_id
     where p_program is null
  ),
  open_runs as (
    select u.user_id, u.case_prefix from public.runs u
     where u.status = 'in_progress' and u.user_id in (select user_id from people)
  )
  select jsonb_build_object(
    'generated_at', now(),
    'first_only', p_first,
    'days', p_days,
    'named', v_named,
    'staff', v_staff,
    'program', case when p_program is null then null else jsonb_build_object(
        'id', v_prog.id, 'name', v_prog.name, 'status', v_prog.status, 'join_code', v_prog.join_code,
        'show_named_results', v_prog.show_named_results, 'all_cases', v_prog.all_cases, 'seats', v_prog.seats,
        'cases', coalesce((select jsonb_agg(c.case_prefix order by c.case_prefix)
                             from public.program_cases c where c.program_id = v_prog.id), '[]'::jsonb)) end,
    'totals', (select jsonb_build_object(
        'people', (select count(*) from people),
        'residents', (select count(*) from people where role <> 'admin'),
        'active_30d', (select count(distinct user_id) from rec where finished_at > now() - interval '30 days'),
        'with_a_finished_run', (select count(distinct user_id) from rec),
        'runs', (select count(*) from rec),
        'first_attempts', (select count(*) from rec where attempt_no = 1),
        'open_runs', (select count(*) from open_runs))),
    -- Completion is always by name. Results by name only when the switch allows it.
    'members', coalesce((select jsonb_agg(jsonb_build_object(
          'user_id', p.user_id, 'name', p.display_name, 'pgy', p.pgy, 'role', p.role, 'joined_at', p.joined_at,
          'cases_finished', (select count(distinct case_prefix) from rec where rec.user_id = p.user_id),
          'runs', (select count(*) from rec where rec.user_id = p.user_id),
          'open', (select count(*) from open_runs o where o.user_id = p.user_id),
          'case_minutes', (select coalesce(round(sum(sim_seconds) / 60.0), 0) from rec where rec.user_id = p.user_id),
          'last_finished', (select max(finished_at) from rec where rec.user_id = p.user_id),
          'cases', (select coalesce(jsonb_agg(distinct case_prefix), '[]'::jsonb) from rec where rec.user_id = p.user_id),
          'results', case when v_named then (select jsonb_build_object(
              'n', count(*), 'met', count(*) filter (where result = 'met'),
              'met_prompted', count(*) filter (where result = 'met_prompted'),
              'not_met', count(*) filter (where result = 'not_met'),
              'harmful', count(*) filter (where 'harmful_action' = any (why)),
              'lost', count(*) filter (where 'case_lost' = any (why)))
            from sel where sel.user_id = p.user_id) end)
        order by p.display_name nulls last, p.user_id) from people p), '[]'::jsonb),
    'cases', coalesce((select jsonb_agg(c order by c ->> 'case_prefix') from (
        select jsonb_build_object(
          'case_prefix', s.case_prefix, 'n', count(*), 'learners', count(distinct s.user_id),
          'met', count(*) filter (where s.result = 'met'),
          'met_prompted', count(*) filter (where s.result = 'met_prompted'),
          'not_met', count(*) filter (where s.result = 'not_met'),
          'harmful', count(*) filter (where 'harmful_action' = any (s.why)),
          'lost', count(*) filter (where 'case_lost' = any (s.why)),
          'median_seconds', percentile_cont(0.5) within group (order by s.sim_seconds),
          'open', (select count(*) from open_runs o where o.case_prefix = s.case_prefix)) as c
        from sel s group by s.case_prefix) q), '[]'::jsonb),
    -- Expected actions: how often done, how often only after a prompt, and how long it took.
    'items', coalesce((select jsonb_agg(c) from (
        select jsonb_build_object(
          'case_prefix', s.case_prefix, 'kind', i.kind, 'item_id', i.item_id,
          'tab', max(i.tab), 'cat', max(i.cat), 'grp', max(i.grp),
          'n', count(*), 'done', count(*) filter (where i.result = 'done'),
          'prompted', count(*) filter (where i.result = 'done' and i.prompted),
          'learners_missed', count(distinct s.user_id) filter (where i.result = 'missed'),
          'median_delay', percentile_cont(0.5) within group (order by i.done_t - i.expected_t)
                            filter (where i.result = 'done' and i.done_t is not null and i.expected_t is not null)) as c
        from sel s join public.run_items i on i.run_id = s.run_id
       where i.kind in ('critical', 'recommended')
       group by s.case_prefix, i.kind, i.item_id) q), '[]'::jsonb),
    'safety', coalesce((select jsonb_agg(c) from (
        select jsonb_build_object(
          'case_prefix', s.case_prefix, 'kind', i.kind, 'item_id', i.item_id,
          'tab', max(i.tab), 'cat', max(i.cat), 'grp', max(i.grp),
          'runs', count(*), 'learners', count(distinct s.user_id)) as c
        from sel s join public.run_items i on i.run_id = s.run_id
       where i.kind in ('discouraged', 'harmful')
       group by s.case_prefix, i.kind, i.item_id) q), '[]'::jsonb),
    'handoff', coalesce((select jsonb_agg(c) from (
        select jsonb_build_object(
          'case_prefix', s.case_prefix, 'kind', i.kind, 'item_id', i.item_id, 'result', i.result,
          'n', count(*)) as c
        from sel s join public.run_items i on i.run_id = s.run_id
       where i.kind in ('diagnosis', 'disposition')
       group by s.case_prefix, i.kind, i.item_id, i.result) q), '[]'::jsonb),
    'months', coalesce((select jsonb_agg(c order by c ->> 'month') from (
        select jsonb_build_object(
          'month', to_char(date_trunc('month', s.finished_at), 'YYYY-MM'), 'n', count(*),
          'met', count(*) filter (where s.result = 'met'),
          'met_prompted', count(*) filter (where s.result = 'met_prompted'),
          'not_met', count(*) filter (where s.result = 'not_met')) as c
        from sel s group by date_trunc('month', s.finished_at)) q), '[]'::jsonb),
    'years', coalesce((select jsonb_agg(c order by (c ->> 'pgy')::int nulls last) from (
        select jsonb_build_object(
          'pgy', s.pgy, 'n', count(*), 'learners', count(distinct s.user_id),
          'met', count(*) filter (where s.result = 'met'),
          'met_prompted', count(*) filter (where s.result = 'met_prompted'),
          'not_met', count(*) filter (where s.result = 'not_met')) as c
        from sel s group by s.pgy) q), '[]'::jsonb)
  ) into v_out;
  return v_out;
end;
$$;

-- ---------------------------------------------------------------- staff tools
create or replace function public.new_join_code()
returns text language plpgsql volatile security definer set search_path = '' as $$
declare
  v_abc  constant text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  v_code text;
  v_b    bytea;
begin
  loop
    v_b := uuid_send(gen_random_uuid());
    -- Bytes 6 and 8 of a version 4 UUID are partly fixed, so they are not used.
    select string_agg(substr(v_abc, 1 + (get_byte(v_b, i) % 32), 1), '' order by i) into v_code
      from unnest(array[0, 1, 2, 3, 4, 5, 7, 10]) as t(i);
    exit when not exists (select 1 from public.programs where join_code = v_code);
  end loop;
  return v_code;
end;
$$;
revoke all on function public.new_join_code() from public, anon, authenticated;

-- Every program with its numbers, and the settings. Staff only.
create or replace function public.staff_overview()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.is_staff() then raise exception 'not allowed' using errcode = '42501'; end if;
  return jsonb_build_object(
    'settings', (select jsonb_build_object('enforce_entitlements', enforce_entitlements, 'free_cases', to_jsonb(free_cases))
                   from public.app_settings where id),
    'accounts', (select count(*) from public.profiles),
    'individuals', (select count(*) from public.profiles p
                     where not exists (select 1 from public.program_members m where m.user_id = p.user_id)),
    'records', (select count(*) from public.run_records),
    'programs', coalesce((select jsonb_agg(jsonb_build_object(
        'id', g.id, 'name', g.name, 'status', g.status, 'join_code', g.join_code,
        'show_named_results', g.show_named_results, 'all_cases', g.all_cases, 'seats', g.seats,
        'created_at', g.created_at,
        'cases', coalesce((select jsonb_agg(c.case_prefix order by c.case_prefix)
                             from public.program_cases c where c.program_id = g.id), '[]'::jsonb),
        'residents', (select count(*) from public.program_members m where m.program_id = g.id and m.role = 'resident'),
        'admins', (select count(*) from public.program_members m where m.program_id = g.id and m.role = 'admin'),
        'runs', (select count(*) from public.run_records r where r.program_id = g.id),
        'last_finished', (select max(u.finished_at) from public.run_records r join public.runs u on u.id = r.run_id
                           where r.program_id = g.id)) order by g.name) from public.programs g), '[]'::jsonb));
end;
$$;

-- Creates a program (p_id null) or changes one. Returns its id. Staff only.
create or replace function public.staff_save_program(
  p_id uuid, p_name text, p_named boolean, p_all_cases boolean, p_cases text[], p_seats integer, p_status text)
returns uuid language plpgsql security definer set search_path = '' as $$
declare
  v_id uuid := p_id;
begin
  if not public.is_staff() then raise exception 'not allowed' using errcode = '42501'; end if;
  if v_id is null then
    insert into public.programs (name, join_code, show_named_results, all_cases, seats, status)
    values (btrim(p_name), public.new_join_code(), coalesce(p_named, true), coalesce(p_all_cases, true),
            p_seats, coalesce(p_status, 'active'))
    returning id into v_id;
  else
    update public.programs
       set name = coalesce(nullif(btrim(p_name), ''), name),
           show_named_results = coalesce(p_named, show_named_results),
           all_cases = coalesce(p_all_cases, all_cases),
           seats = p_seats,
           status = coalesce(p_status, status)
     where id = v_id;
    if not found then raise exception 'no such program' using errcode = 'P0002'; end if;
  end if;
  if p_cases is not null then
    delete from public.program_cases where program_id = v_id;
    insert into public.program_cases (program_id, case_prefix)
    select distinct v_id, x from unnest(p_cases) x where x ~ '^[A-Z][A-Z0-9]{1,15}$';
  end if;
  return v_id;
end;
$$;

-- A new join code for a program. The old one stops working at once. Staff only.
create or replace function public.staff_new_code(p_id uuid)
returns text language plpgsql security definer set search_path = '' as $$
declare
  v_code text;
begin
  if not public.is_staff() then raise exception 'not allowed' using errcode = '42501'; end if;
  v_code := public.new_join_code();
  update public.programs set join_code = v_code where id = p_id;
  if not found then raise exception 'no such program' using errcode = 'P0002'; end if;
  return v_code;
end;
$$;

-- Staff: set a member's role ('resident' or 'admin'), or remove them (p_role 'remove').
-- A program's admin: remove a resident from their own program, nothing else.
-- A removed member's finished runs stay in the program's data.
create or replace function public.program_set_member(p_user uuid, p_role text)
returns text language plpgsql security definer set search_path = '' as $$
declare
  v_uid   uuid := (select auth.uid());
  v_staff boolean := public.is_staff();
  v_m     public.program_members%rowtype;
begin
  if v_uid is null then raise exception 'sign in first' using errcode = '42501'; end if;
  select * into v_m from public.program_members where user_id = p_user;
  if not found then return 'no_member'; end if;
  if not v_staff then
    if p_role is distinct from 'remove' or v_m.role <> 'resident' or not exists (
         select 1 from public.program_members a
          where a.user_id = v_uid and a.program_id = v_m.program_id and a.role = 'admin') then
      raise exception 'not allowed' using errcode = '42501';
    end if;
  end if;
  if p_role = 'remove' then
    delete from public.program_members where user_id = p_user;
  elsif p_role in ('resident', 'admin') then
    update public.program_members set role = p_role where user_id = p_user;
  else
    return 'bad_role';
  end if;
  return 'ok';
end;
$$;

-- Turn entitlement checks on or off, and name the cases every account may open. Staff only.
create or replace function public.staff_set_settings(p_enforce boolean, p_free text[])
returns void language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_staff() then raise exception 'not allowed' using errcode = '42501'; end if;
  update public.app_settings
     set enforce_entitlements = coalesce(p_enforce, enforce_entitlements),
         free_cases = coalesce((select array_agg(distinct x) from unnest(p_free) x where x ~ '^[A-Z][A-Z0-9]{1,15}$'),
                               case when p_free is null then free_cases else '{}' end)
   where id;
end;
$$;

do $$
declare f text;
begin
  foreach f in array array[
    'public.my_program()', 'public.join_program(text, text, integer)',
    'public.record_run(uuid, jsonb, jsonb)', 'public.program_analytics(uuid, boolean, integer)',
    'public.staff_overview()', 'public.staff_save_program(uuid, text, boolean, boolean, text[], integer, text)',
    'public.staff_new_code(uuid)', 'public.program_set_member(uuid, text)',
    'public.staff_set_settings(boolean, text[])']
  loop
    execute format('revoke all on function %s from public, anon', f);
    execute format('grant execute on function %s to authenticated', f);
  end loop;
end $$;
