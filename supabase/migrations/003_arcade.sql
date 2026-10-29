-- EMSim: Ambulance Run leaderboard (29 October 2026).
--
-- Applied through the Supabase connector as migration 003_arcade, after 002_runs. It is safe
-- to run again: every statement checks for what already exists or replaces itself.
--
-- Owner request, 29 October 2026: a small ambulance game on the case list with "a
-- leaderboard if you are in top 10 that will be shared across all accounts and you can choose
-- what your name is."
--
-- What it creates:
--   public.arcade_runs      one row per run a signed-in player starts. A row gets a score
--                           and a name only when the player posts it.
--   public.arcade_start()   starts a run and returns its id. The server keeps the start time.
--   public.arcade_finish()  posts a score and a name for one of the caller's runs. Refuses a
--                           score higher than the time since the start allows. Returns the
--                           top 10.
--   public.arcade_top()     the top 10: name, score, when, and whether it is the caller's.
--
-- Who can do what:
--   - anyone, signed in or not, can read the top 10 (arcade_top). Names and scores are public
--     by design. No email, no user id, nothing else about the account leaves the database.
--   - posting needs a signed-in, confirmed, non-anonymous account with an active profile,
--     the same accounts that can open cases.
--   - the browser has no direct access to the table. Everything goes through the three
--     functions.
--
-- Limits, so a script cannot fill the table or post an impossible score:
--   - a score can be at most v_rate points a second since arcade_start, plus 50. The game's
--     top speed is 72 points a second (engine/arcade.js, RULES.vmax), and
--     engine/arcade-tests.js checks that v_rate allows it. A determined cheat can still post
--     a high score by waiting. This is a game, not a record anyone relies on.
--   - one run start every 2 seconds per account, and at most 300 a day.
--   - runs never posted are deleted after 6 hours. Posted scores outside the best 100 are
--     deleted when a new score is posted.
--   - names are 1 to 16 characters: letters, digits, spaces and . _ ! ? ' -
--
-- Names are not screened for offensive words. To remove one:
--   delete from public.arcade_runs where name = 'THE NAME';
-- Deleting an account deletes its runs.

create table if not exists public.arcade_runs (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users (id) on delete cascade,
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  score       integer check (score between 0 and 100000000),
  name        text check (name is null or (char_length(name) between 1 and 16 and name ~ '^[A-Za-z0-9 ._!?''-]+$')),
  constraint arcade_runs_shape check ((finished_at is null and score is null and name is null)
                                   or (finished_at is not null and score is not null and name is not null))
);
create index if not exists arcade_runs_board on public.arcade_runs (score desc, finished_at asc)
  where finished_at is not null;
create index if not exists arcade_runs_user on public.arcade_runs (user_id, started_at desc);

alter table public.arcade_runs enable row level security;
revoke all on table public.arcade_runs from anon, authenticated;
-- No policies: with row-level security on and no grants, the browser cannot touch the table.

-- The caller, if they may post: signed in, confirmed, not anonymous, active profile.
create or replace function public.arcade_caller()
returns uuid
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_ok  boolean;
begin
  if v_uid is null then
    raise exception 'sign in to post scores' using errcode = '42501';
  end if;
  select (u.email_confirmed_at is not null and not coalesce(u.is_anonymous, false)
          and exists (select 1 from public.profiles p where p.user_id = u.id and p.status = 'active'))
    into v_ok
    from auth.users u where u.id = v_uid;
  if not coalesce(v_ok, false) then
    raise exception 'this account cannot post scores' using errcode = '42501';
  end if;
  return v_uid;
end;
$$;
revoke all on function public.arcade_caller() from public, anon, authenticated;

create or replace function public.arcade_top()
returns table (name text, score integer, finished_at timestamptz, mine boolean)
language sql
stable
security definer
set search_path = ''
as $$
  select r.name, r.score, r.finished_at, (r.user_id = auth.uid()) as mine
    from public.arcade_runs r
   where r.finished_at is not null
   order by r.score desc, r.finished_at asc
   limit 10;
$$;
revoke all on function public.arcade_top() from public;
grant execute on function public.arcade_top() to anon, authenticated;

create or replace function public.arcade_start()
returns uuid
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_uid  uuid := public.arcade_caller();
  v_last timestamptz;
  v_day  integer;
  v_id   uuid;
begin
  delete from public.arcade_runs
   where user_id = v_uid and finished_at is null and started_at < now() - interval '6 hours';
  select max(started_at), count(*) filter (where started_at > now() - interval '1 day')
    into v_last, v_day
    from public.arcade_runs where user_id = v_uid;
  if v_last is not null and v_last > now() - interval '2 seconds' then
    raise exception 'runs started too quickly' using errcode = 'P0001';
  end if;
  if v_day >= 300 then
    raise exception 'too many runs today' using errcode = 'P0001';
  end if;
  insert into public.arcade_runs (user_id) values (v_uid) returning id into v_id;
  return v_id;
end;
$$;
revoke all on function public.arcade_start() from public, anon;
grant execute on function public.arcade_start() to authenticated;

create or replace function public.arcade_finish(p_run uuid, p_score integer, p_name text)
returns table (name text, score integer, finished_at timestamptz, mine boolean)
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_uid     uuid := public.arcade_caller();
  v_rate    constant numeric := 80;   -- points a second allowed; the game's top speed is 72
  v_started timestamptz;
  v_name    text := regexp_replace(btrim(coalesce(p_name, '')), '\s+', ' ', 'g');
begin
  select r.started_at into v_started
    from public.arcade_runs r
   where r.id = p_run and r.user_id = v_uid and r.finished_at is null
   for update;
  if v_started is null then
    raise exception 'no such run' using errcode = 'P0002';
  end if;
  if p_score is null or p_score < 1 then
    raise exception 'no score' using errcode = '22023';
  end if;
  if p_score > v_rate * extract(epoch from (now() - v_started)) + 50 then
    raise exception 'score not possible' using errcode = '22023';
  end if;
  if char_length(v_name) not between 1 and 16 or v_name !~ '^[A-Za-z0-9 ._!?''-]+$' then
    raise exception 'name not allowed' using errcode = '22023';
  end if;
  update public.arcade_runs r
     set finished_at = now(), score = p_score, name = upper(v_name)
   where r.id = p_run;
  delete from public.arcade_runs r
   where r.finished_at is not null
     and r.id not in (select b.id from public.arcade_runs b where b.finished_at is not null
                       order by b.score desc, b.finished_at asc limit 100);
  return query
    select b.name, b.score, b.finished_at, (b.user_id = v_uid)
      from public.arcade_runs b
     where b.finished_at is not null
     order by b.score desc, b.finished_at asc
     limit 10;
end;
$$;
revoke all on function public.arcade_finish(uuid, integer, text) from public, anon;
grant execute on function public.arcade_finish(uuid, integer, text) to authenticated;
