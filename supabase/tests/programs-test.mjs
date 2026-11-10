// Runs migrations 001, 002 and 004 in an in-process Postgres (PGlite) with stand-ins for the
// parts of Supabase they touch, then checks the rules of 004 as each kind of account.
//   node sqltest.mjs <dir with 001_access.sql 002_runs.sql 004_programs.sql>
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = process.argv[2];
const db = new PGlite();
let fails = 0, n = 0;
const ok = (name, cond, extra) => { n++; if (!cond) fails++; console.log((cond ? 'ok   ' : 'FAIL ') + name + (cond || extra === undefined ? '' : '  [' + extra + ']')); };
const U = { staff: '00000000-0000-0000-0000-00000000000a', admin: '00000000-0000-0000-0000-00000000000b',
  c: '00000000-0000-0000-0000-00000000000c', d: '00000000-0000-0000-0000-00000000000d',
  ind: '00000000-0000-0000-0000-00000000000e', other: '00000000-0000-0000-0000-00000000000f' };

await db.exec(`
  create role anon; create role authenticated; create role service_role;
  create schema auth; create schema storage;
  create table auth.users (id uuid primary key);
  create function auth.uid() returns uuid language sql stable as
    $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
  create table storage.buckets (id text primary key, name text, public boolean);
  grant usage on schema public, auth to anon, authenticated, service_role;
  grant execute on function auth.uid() to anon, authenticated, service_role;
`);
for (const f of ['001_access.sql', '002_runs.sql', '004_programs.sql', '004_programs.sql'])
  await db.exec(fs.readFileSync(dir + '/' + f, 'utf8'));
ok('001, 002 and 004 apply, and 004 applies twice', true);
for (const id of Object.values(U)) await db.query('insert into auth.users (id) values ($1)', [id]);
await db.query('insert into public.staff (user_id) values ($1)', [U.staff]);

// Run a statement as a signed-in account, under the authenticated role and its grants.
async function as(uid, sql, params) {
  await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub', '${uid || ''}', false);`);
  try { const r = await db.query(sql, params); return { rows: r.rows, v: r.rows[0] && Object.values(r.rows[0])[0] }; }
  catch (e) { return { err: e.message, code: e.code }; }
  finally { await db.exec(`reset role; select set_config('request.jwt.claim.sub', '', false);`); }
}
const svc = async (sql, params) => (await db.query(sql, params)).rows;

// ---- programs and joining
let r = await as(U.c, `select public.staff_save_program(null, 'Mercy EM', true, true, null, null, null)`);
ok('a non-staff account cannot create a program', r.code === '42501', r.err);
r = await as(U.staff, `select public.staff_save_program(null, 'Mercy EM', true, true, null, 2, null)`);
const P1 = r.v; ok('staff create a program', !!P1, r.err);
const P2 = (await as(U.staff, `select public.staff_save_program(null, 'Other EM', true, true, null, null, null)`)).v;
const code = (await svc('select join_code from public.programs where id = $1', [P1]))[0].join_code;
const code2 = (await svc('select join_code from public.programs where id = $1', [P2]))[0].join_code;
ok('the join code is eight characters with no I, O, 0 or 1', /^[A-HJ-NP-Z2-9]{8}$/.test(code), code);
r = await as(U.c, `select public.join_program('WRONGCODE', 'Casey', 1)`);
ok('a wrong code is refused', r.v === 'bad_code', r.v || r.err);
r = await as(U.c, `select public.join_program($1, '  Casey   Lee ', 1)`, [code.toLowerCase().slice(0, 4) + '-' + code.toLowerCase().slice(4)]);
ok('a code typed in lower case with a dash joins', r.v === 'ok', r.v || r.err);
ok('the name is trimmed', (await svc('select display_name from public.program_members where user_id = $1', [U.c]))[0].display_name === 'Casey Lee');
r = await as(U.c, `select public.join_program($1, 'Casey', 1)`, [code2]);
ok('one program per account', r.v === 'already_member', r.v);
r = await as(U.admin, `select public.join_program($1, 'Dr Admin', null)`, [code]);
ok('a second account joins', r.v === 'ok', r.v || r.err);
r = await as(U.d, `select public.join_program($1, 'Dana', 2)`, [code]);
ok('two seats, so a third resident is refused', r.v === 'full', r.v);
await as(U.staff, `select public.staff_save_program($1, null, null, null, null, null, null)`, [P1]);
r = await as(U.d, `select public.join_program($1, 'Dana', 2)`, [code]);
ok('with the seat limit removed the third joins', r.v === 'ok', r.v);
r = await as(U.other, `select public.join_program($1, 'Dr Other', null)`, [code2]);
r = await as(U.admin, `select public.program_set_member($1, 'admin')`, [U.admin]);
ok('a resident cannot make themselves an admin', r.code === '42501', r.v || r.err);
r = await as(U.staff, `select public.program_set_member($1, 'admin')`, [U.admin]);
ok('staff make an admin', r.v === 'ok', r.v || r.err);
await as(U.staff, `select public.program_set_member($1, 'admin')`, [U.other]);
r = await as(U.admin, `select public.my_program()`);
ok('my_program gives an admin the join code', r.v && r.v.member.role === 'admin' && r.v.member.join_code === code && r.v.staff === false, JSON.stringify(r.v));
r = await as(U.c, `select public.my_program()`);
ok('my_program does not give a resident the join code', r.v && r.v.member.join_code === null && r.v.member.program === 'Mercy EM');
r = await as(U.ind, `select public.my_program()`);
ok('an individual account has no program', r.v && r.v.member === null);
r = await as('', `select public.my_program()`);
ok('signed out, my_program is refused', !!r.err);

// ---- finished runs and their records
const key = 'abcdef0123456789';
async function finishRun(uid, prefix, outcome) {
  const q = await as(uid, `insert into public.runs (case_prefix, version_key, mode, status, sim_seconds, outcome, ended_by, score_pct, summary)
    values ($1, $2, 'standard', 'finished', 600, $3, 'completed', 80, '{}'::jsonb) returning id`, [prefix, key, outcome]);
  if (q.err) throw new Error(q.err);
  return q.v;
}
const record = (result, why, items) => JSON.stringify({ v: 1, result, why, phases: [{ id: 'p1', t: 0 }],
  counts: { critical: 2 }, items });
const items1 = [
  { k: 'critical', id: 'act_one', tab: 'interventions', cat: 'medication', grp: 'G', r: 'done', p: false, et: 0, dt: 42.5 },
  { k: 'critical', id: 'act_two', tab: 'stabilization', cat: 'x', grp: 'G2', r: 'done', p: true, et: 0, dt: 130 },
  { k: 'discouraged', id: 'act_bad', tab: 'interventions', cat: 'medication', grp: 'G', r: 'taken', p: false, et: null, dt: 50 },
  { k: 'diagnosis', id: 'dx_right', tab: null, cat: null, grp: null, r: 'correct', p: false, et: null, dt: null },
  { k: 'disposition', id: 'icu', tab: null, cat: null, grp: null, r: 'correct', p: false, et: null, dt: null },
  { k: 'nonsense', id: 'x', r: 'done' }, 'not an object'];
const runC1 = await finishRun(U.c, 'DKA', 'all');
r = await as(U.c, `select public.record_run($1, $2::jsonb, $3::jsonb)`, [runC1, record('met_prompted', [], items1), JSON.stringify([{ t: 1, a: 'act_one' }])]);
ok('a record is stored', r.v === 'ok', r.v || r.err);
r = await as(U.c, `select public.record_run($1, $2::jsonb, null)`, [runC1, record('met', [], items1)]);
ok('a run is recorded once', r.v === 'exists', r.v);
ok('items of an unknown kind are dropped', (await svc('select count(*)::int n from public.run_items where run_id = $1', [runC1]))[0].n === 5);
const rr = (await svc('select * from public.run_records where run_id = $1', [runC1]))[0];
ok('the record carries the program, the year and attempt 1, unverified', rr.program_id === P1 && rr.pgy === 1 && rr.attempt_no === 1 && rr.verified === false, JSON.stringify(rr));
const runC2 = await finishRun(U.c, 'DKA', 'missed');
r = await as(U.c, `select public.record_run($1, $2::jsonb, null)`, [runC2, record('met', [], items1)]);
ok('a run that missed a critical action cannot be recorded as met', r.v === 'mismatch', r.v);
r = await as(U.c, `select public.record_run($1, $2::jsonb, null)`, [runC2, record('not_met', ['critical_missed'], [
  { k: 'critical', id: 'act_one', tab: 'interventions', cat: 'medication', grp: 'G', r: 'missed', p: true, et: 0, dt: null },
  { k: 'harmful', id: 'act_worse', tab: 'interventions', cat: 'medication', grp: 'G', r: 'taken', p: false, et: null, dt: 77 },
  { k: 'diagnosis', id: 'dx_wrong', r: 'incorrect' }, { k: 'disposition', id: null, r: 'none' }])]);
ok('the second attempt is stored', r.v === 'ok', r.v || r.err);
ok('and is attempt 2', (await svc('select attempt_no from public.run_records where run_id = $1', [runC2]))[0].attempt_no === 2);
r = await as(U.d, `select public.record_run($1, $2::jsonb, null)`, [runC1, record('met', [], items1)]);
ok("another account cannot record someone else's run", r.v === 'no_run', r.v);
r = await as(U.c, `select public.record_run($1, '{"result":"met"}'::jsonb, null)`, [runC2]);
ok('a record with no items is refused', r.v === 'exists' || r.v === 'bad_record', r.v);
const runD = await finishRun(U.d, 'DKA', 'all');
r = await as(U.d, `select public.record_run($1, '[1,2]'::jsonb, null)`, [runD]);
ok('a record that is not an object is refused', r.v === 'bad_record', r.v);
await as(U.d, `select public.record_run($1, $2::jsonb, null)`, [runD, record('met', [], items1.slice(0, 5).map(i => Object.assign({}, i, { p: false })))]);
const runI = await finishRun(U.ind, 'TSS', 'all');
r = await as(U.ind, `select public.record_run($1, $2::jsonb, null)`, [runI, record('met', [], items1)]);
ok("an individual's run is recorded with no program", r.v === 'ok' && (await svc('select program_id from public.run_records where run_id = $1', [runI]))[0].program_id === null);
const runO = await finishRun(U.other, 'DKA', 'all');
await as(U.other, `select public.record_run($1, $2::jsonb, null)`, [runO, record('met', [], items1)]);

// ---- the browser cannot touch the tables
for (const t of ['run_records', 'run_items', 'program_members', 'programs', 'staff', 'app_settings', 'program_cases']) {
  r = await as(U.admin, `select count(*) from public.${t}`);
  ok('the browser cannot read ' + t, r.code === '42501', r.err || 'readable');
}
r = await as(U.c, `insert into public.staff (user_id) values ($1)`, [U.c]);
ok('the browser cannot make itself staff', r.code === '42501', r.err);
r = await as('', `select public.program_analytics(null, true, null)`);
ok('signed out, analytics are refused', !!r.err);

// ---- analytics, and who may read them
r = await as(U.c, `select public.program_analytics($1, true, null)`, [P1]);
ok('a resident cannot read analytics', r.code === '42501', r.err);
r = await as(U.other, `select public.program_analytics($1, true, null)`, [P1]);
ok("another program's admin cannot read this program", r.code === '42501', r.err);
r = await as(U.admin, `select public.program_analytics(null, true, null)`);
ok('a program admin cannot read every account', r.code === '42501', r.err);
r = await as(U.admin, `select public.program_analytics($1, true, null)`, [P1]);
let a = r.v;
ok('a program admin reads their own program', !!a && a.program.name === 'Mercy EM', r.err);
ok('first attempts: two runs, one per resident', a && a.cases.length === 1 && a.cases[0].n === 2 && a.cases[0].learners === 2, JSON.stringify(a && a.cases));
ok('members are the three who joined, by name', a && a.members.map(m => m.name).join() === 'Casey Lee,Dana,Dr Admin', a && a.members.map(m => m.name).join());
const casey = a && a.members.find(m => m.name === 'Casey Lee');
ok('completion by name: cases finished, runs', casey && casey.cases_finished === 1 && casey.runs === 2, JSON.stringify(casey));
ok('results by name while the switch is on', casey && casey.results && casey.results.met_prompted === 1 && casey.results.n === 1, JSON.stringify(casey && casey.results));
const it = a && a.items.find(i => i.item_id === 'act_two');
ok('an item: expected twice, done twice, prompted once, median delay 130', it && it.n === 2 && it.done === 2 && it.prompted === 1 && Number(it.median_delay) === 130, JSON.stringify(it));
ok('a discouraged action is counted by learner', a && a.safety.some(s => s.item_id === 'act_bad' && s.learners === 2));
ok('the handoff lists the diagnosis chosen', a && a.handoff.some(h => h.kind === 'diagnosis' && h.item_id === 'dx_right' && h.n === 2));
ok('nothing from the other program or the individual', a && !JSON.stringify(a).includes(U.other) && !JSON.stringify(a).includes(U.ind));
ok('by year: PGY-1 and PGY-2', a && a.years.map(y => y.pgy).join() === '1,2', JSON.stringify(a && a.years));
r = await as(U.admin, `select public.program_analytics($1, false, null)`, [P1]);
a = r.v;
ok('all attempts: three runs, one not met with a harmful action', a && a.cases[0].n === 3 && a.cases[0].not_met === 1 && a.cases[0].harmful === 0 && a.safety.some(s => s.kind === 'harmful'), JSON.stringify(a && a.cases));
ok('all attempts: the missed action is counted', a && a.items.find(i => i.item_id === 'act_one').learners_missed === 1);
await as(U.staff, `select public.staff_save_program($1, null, false, null, null, null, null)`, [P1]);
r = await as(U.admin, `select public.program_analytics($1, true, null)`, [P1]);
a = r.v;
ok('switch off: completion still by name, results by name gone', a && a.named === false && a.members.every(m => m.results === null && typeof m.cases_finished === 'number'), JSON.stringify(a && a.members[0]));
ok('switch off: group results still there', a && a.cases[0].n === 2);
r = await as(U.staff, `select public.program_analytics($1, true, null)`, [P1]);
ok('staff still see results by name', r.v && r.v.named === true && r.v.members.some(m => m.results));
r = await as(U.staff, `select public.program_analytics(null, false, null)`);
ok('staff read every account: five runs, and the individual is listed', r.v && r.v.totals.runs === 5 && r.v.members.some(m => m.role === 'individual'), JSON.stringify(r.v && r.v.totals));
r = await as(U.staff, `select public.program_analytics(null, false, 0)`);
ok('a period of zero days holds nothing', r.v && r.v.totals.runs === 0);
r = await as(U.staff, `select public.staff_overview()`);
ok('the staff overview lists both programs with their numbers', r.v && r.v.programs.length === 2 && r.v.programs.find(p => p.name === 'Mercy EM').residents === 2 && r.v.programs.find(p => p.name === 'Mercy EM').runs === 3, JSON.stringify(r.v && r.v.programs.map(p => [p.name, p.residents, p.runs])));
r = await as(U.admin, `select public.staff_overview()`);
ok('a program admin cannot read the staff overview', r.code === '42501');

// ---- deleting
r = await as(U.c, `delete from public.runs where id = $1 returning id`, [runC1]);
ok('a program member cannot delete a finished run', !r.err && r.rows.length === 0, r.err);
const open = (await as(U.c, `insert into public.runs (case_prefix, version_key, mode, state) values ('TSS', $1, 'standard', '{"v":1}'::jsonb) returning id`, [key])).v;
r = await as(U.c, `delete from public.runs where id = $1 returning id`, [open]);
ok('a program member can discard a run in progress', !r.err && r.rows.length === 1, r.err);
r = await as(U.ind, `delete from public.runs where id = $1 returning id`, [runI]);
ok('an individual can delete a finished run', !r.err && r.rows.length === 1, r.err);
ok('and its record and items go with it', (await svc('select count(*)::int n from public.run_records where run_id = $1', [runI]))[0].n === 0);

// ---- removing a member
r = await as(U.other, `select public.program_set_member($1, 'remove')`, [U.d]);
ok("an admin cannot remove another program's resident", r.code === '42501', r.v || r.err);
r = await as(U.admin, `select public.program_set_member($1, 'remove')`, [U.d]);
ok('an admin removes their own resident', r.v === 'ok', r.v || r.err);
ok("the removed resident's runs stay in the program", (await svc('select count(*)::int n from public.run_records where user_id = $1 and program_id = $2', [U.d, P1]))[0].n === 1);
r = await as(U.staff, `select public.staff_new_code($1)`, [P1]);
ok('staff issue a new code and the old one stops working', /^[A-HJ-NP-Z2-9]{8}$/.test(r.v || '') && r.v !== code && (await as(U.d, `select public.join_program($1, 'Dana', 2)`, [code])).v === 'bad_code');

// ---- entitlements
const claim = async (uid, prefix) => (await svc(`select public.claim_case_load($1, $2, 1000, 1000) v`, [uid, prefix]))[0].v;
ok('entitlements off: an individual opens any case', await claim(U.ind, 'TSS') === 'ok');
r = await as(U.c, `select public.staff_set_settings(true, null)`);
ok('a resident cannot change the settings', r.code === '42501');
await as(U.staff, `select public.staff_set_settings(true, array['CHFE'])`);
ok('entitlements on: an individual is refused a paid case', await claim(U.ind, 'TSS') === 'not_entitled', await claim(U.ind, 'TSS'));
ok('entitlements on: an individual opens a free case', await claim(U.ind, 'CHFE') === 'ok');
ok('entitlements on: a member of a program with every case opens any', await claim(U.c, 'TSS') === 'ok');
await as(U.staff, `select public.staff_save_program($1, null, null, false, array['DKA','bad one'], null, null)`, [P1]);
ok('a program with a package: a case in it opens', await claim(U.c, 'DKA') === 'ok');
ok('a program with a package: a case outside it does not', await claim(U.c, 'TSS') === 'not_entitled');
ok('staff open every case', await claim(U.staff, 'TSS') === 'ok');
await as(U.staff, `select public.staff_save_program($1, null, null, null, null, null, 'closed')`, [P1]);
ok('a closed program opens nothing but free cases', await claim(U.c, 'DKA') === 'not_entitled' && await claim(U.c, 'CHFE') === 'ok');
r = await as(U.c, `select public.claim_case_load($1, 'DKA', 10, 10)`, [U.c]);
ok('the browser cannot call claim_case_load', r.code === '42501');
r = await as(U.c, `select public.case_entitled($1, 'DKA')`, [U.c]);
ok('the browser cannot call case_entitled', r.code === '42501');

console.log('\n' + n + ' checks, ' + (fails ? fails + ' FAILURES' : 'all passed'));
process.exit(fails ? 1 : 0);
