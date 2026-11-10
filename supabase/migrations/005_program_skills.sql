-- EMSim: program_skills, for the Teaching priorities tab (10 November 2026).
--
-- Applied through the Supabase connector as migration 005_program_skills, after 004_programs.
-- Safe to run again: it only replaces one function.
--
-- Owner, 10 November 2026: "The gap map is not insightful. Try to reimagine it." The gap map
-- crossed the case's topic with the ordering tab. Neither is something a program can teach
-- to. This function gathers the same critical actions by skill area instead: the group the
-- catalog files the action under (vasoactive agents, oxygen, imaging and so on), which is
-- stored on every run item as `grp`. It answers two questions the first function could not:
--   skills        for each skill area, how many chances there were, how many were done, how
--                 many only after a prompt, how many learners had a chance, how many of them
--                 lost one (missed it, or needed the prompt), and across how many cases.
--   skill_years   the same counts for each skill area and year of training, so the page can
--                 show whether a gap closes as residents advance.
--
-- A chance is one critical action expected in one run. The caller rules and the three
-- arguments are the same as program_analytics: a program's admin for their own program,
-- staff for any program or (p_program null) every account.
create or replace function public.program_skills(
  p_program uuid default null, p_first boolean default true, p_days integer default null)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
  v_uid   uuid := (select auth.uid());
  v_staff boolean;
  v_out   jsonb;
begin
  if v_uid is null then raise exception 'sign in first' using errcode = '42501'; end if;
  v_staff := exists (select 1 from public.staff s where s.user_id = v_uid);
  if p_program is null then
    if not v_staff then raise exception 'not allowed' using errcode = '42501'; end if;
  elsif not v_staff and not exists (select 1 from public.program_members m
                                     where m.user_id = v_uid and m.program_id = p_program and m.role = 'admin') then
    raise exception 'not allowed' using errcode = '42501';
  end if;

  with it as (
    select r.user_id, r.pgy, r.case_prefix, coalesce(nullif(i.grp, ''), 'Other') as grp,
           (i.result = 'done') as done, (i.result = 'done' and i.prompted) as prompted
      from public.run_records r
      join public.runs u on u.id = r.run_id
      join public.run_items i on i.run_id = r.run_id
     where i.kind = 'critical'
       and (p_program is null or r.program_id = p_program)
       and (not p_first or r.attempt_no = 1)
       and (p_days is null or u.finished_at > now() - make_interval(days => p_days))
  )
  select jsonb_build_object(
    'skills', coalesce((select jsonb_agg(c) from (
        select jsonb_build_object(
          'grp', grp, 'n', count(*), 'done', count(*) filter (where done),
          'prompted', count(*) filter (where prompted),
          'learners', count(distinct user_id),
          'learners_lost', count(distinct user_id) filter (where not done or prompted),
          'cases', count(distinct case_prefix)) as c
        from it group by grp) q), '[]'::jsonb),
    'skill_years', coalesce((select jsonb_agg(c) from (
        select jsonb_build_object(
          'grp', grp, 'pgy', pgy, 'n', count(*), 'done', count(*) filter (where done),
          'prompted', count(*) filter (where prompted), 'learners', count(distinct user_id)) as c
        from it group by grp, pgy) q), '[]'::jsonb)
  ) into v_out;
  return v_out;
end;
$$;
revoke all on function public.program_skills(uuid, boolean, integer) from public, anon;
grant execute on function public.program_skills(uuid, boolean, integer) to authenticated;
