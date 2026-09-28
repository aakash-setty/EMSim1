-- EMSim v0.18: invite-only access to case packs.
--
-- Paste this whole file into the Supabase dashboard, SQL Editor, and run it once. It is safe
-- to run again: every statement checks for what already exists.
--
-- What it creates:
--   public.profiles      one row per user, made automatically when a user is created.
--                        status 'active' or 'suspended'; plan 'free' for now.
--   public.case_access   one row per attempt to load a case pack, allowed or not.
--   public.claim_case_load(...)   the rate limit and the log in one call, for the edge
--                        function only. Nobody signed in can call it.
--   storage bucket case-packs     private. Only the edge function reads it.
--
-- Row-level security is on for both tables. A signed-in user can read their own profile
-- and nothing else here. Nobody can write to either table from the browser.

-- ---------------------------------------------------------------- profiles
create table if not exists public.profiles (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  status     text not null default 'active' check (status in ('active', 'suspended')),
  plan       text not null default 'free'   check (plan in ('free', 'paid')),
  created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;

revoke all on table public.profiles from anon, authenticated;
grant select on table public.profiles to authenticated;

drop policy if exists "profiles: read own row" on public.profiles;
create policy "profiles: read own row" on public.profiles
  for select to authenticated
  using ((select auth.uid()) = user_id);

-- A profile for every new user. security definer because auth.users belongs to another
-- role; search_path is empty so every name below is written out in full.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (user_id) values (new.id)
  on conflict (user_id) do nothing;
  return new;
end;
$$;
revoke all on function public.handle_new_user() from public, anon, authenticated;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Users created before this file ran.
insert into public.profiles (user_id)
select id from auth.users
on conflict (user_id) do nothing;

-- ---------------------------------------------------------------- case_access
create table if not exists public.case_access (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users (id) on delete cascade,
  case_prefix text not null,
  allowed     boolean not null,
  reason      text not null,
  created_at  timestamptz not null default now()
);
create index if not exists case_access_user_time on public.case_access (user_id, created_at desc);
alter table public.case_access enable row level security;
revoke all on table public.case_access from anon, authenticated;
-- No policies: the table is invisible to the browser. The edge function uses the secret key.

-- ---------------------------------------------------------------- claim_case_load
-- Returns 'ok', 'rate_limited', 'suspended' or 'no_profile', and logs every attempt except
-- 'no_profile'.
-- Counts only allowed loads, so a user who hits the limit is not held there by their own
-- retries. The advisory lock makes two loads from the same user at the same instant count
-- one after the other instead of both passing.
create or replace function public.claim_case_load(
  p_user uuid, p_prefix text, p_per_hour integer, p_per_day integer)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_status text;
  v_hour   integer;
  v_day    integer;
  v_result text;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_user::text, 0));

  select status into v_status from public.profiles where user_id = p_user;

  if v_status is null then
    v_result := 'no_profile';
  elsif v_status <> 'active' then
    v_result := 'suspended';
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

  -- A user with no profile may not exist in auth.users either, and the log row would then
  -- break its foreign key, so that one case is refused without a log row. Refusals are
  -- logged at most once a minute per user, so a loop of refused requests cannot grow the
  -- table without limit; every allowed load is logged.
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

-- ---------------------------------------------------------------- storage
insert into storage.buckets (id, name, public)
values ('case-packs', 'case-packs', false)
on conflict (id) do update set public = false;
-- No storage policies are created for this bucket, so only the secret key can read it.
