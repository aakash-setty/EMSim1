"use strict";
/* ============================== data ============================== */
const BANK = JSON.parse(document.getElementById("bank").textContent);
const QS = BANK.questions;
const QMAP = Object.fromEntries(QS.map((q, i) => [q.id, Object.assign(q, { _i: i })]));
const CASE_ORDER = ["AFRVR", "CHFE", "DIPH", "MGCA", "ALL"];
const CASEMAP = Object.fromEntries(BANK.cases.map(c => [c.id, c]));
const CASE_SHORT = { ALL: "Cross-case" };
const PRI = { high: 0, medium: 1, low: 2 };
const PRI_LABEL = { high: "High", medium: "Medium", low: "Low" };
const PROV = { seed: ["Physician seed", "--seed"], model: ["Model-drafted", "--model"], "audit-fix": ["Audit fix (model)", "--audit"], mixed: ["Mixed sources", "--mixed"] };
const CATS = [...new Set(QS.map(q => q.category))].sort();
const LS_STATE = "emsim-review-state-v1", LS_UI = "emsim-review-ui-v1", LS_IMPORTS = "emsim-review-imports-v1";

/* ============================== state ============================== */
function blankState() {
  return { v: 1, bank_version: BANK.bank_version, reviewer: { name: "", role: "", disclosures: "" }, answers: {}, flags: {}, updatedAt: 0 };
}
function lsGet(k) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } }
function normalizeState(s) {
  const b = blankState();
  if (!s || typeof s !== "object") return b;
  return { v: 1, bank_version: s.bank_version || BANK.bank_version, reviewer: Object.assign(b.reviewer, s.reviewer || {}), answers: s.answers || {}, flags: s.flags || {}, updatedAt: s.updatedAt || 0 };
}
let S = normalizeState(lsGet(LS_STATE));
const UI = Object.assign({ view: "review", current: null, sort: "priority", filters: { cases: [], pri: "all", status: "all", kind: "all", cat: "all", q: "" }, csFilter: "all" }, lsGet(LS_UI) || {});
UI.filters = Object.assign({ cases: [], pri: "all", status: "all", kind: "all", cat: "all", q: "" }, UI.filters || {});
let IMPORTS = lsGet(LS_IMPORTS) || [];
const HIST = [], FUT = [];
const HIST_MAX = 200;

function snapshot() { return JSON.stringify({ reviewer: S.reviewer, answers: S.answers, flags: S.flags }); }
function restore(json) { const o = JSON.parse(json); S.reviewer = o.reviewer; S.answers = o.answers; S.flags = o.flags; }
function pushHist(label) { HIST.push({ snap: snapshot(), label }); if (HIST.length > HIST_MAX) HIST.shift(); FUT.length = 0; }
function touch() { S.updatedAt = Date.now(); persist(); }
function mutate(label, fn, opts) {
  pushHist(label);
  fn();
  touch();
  if (!opts || opts.render !== false) render();
}
function undo() {
  if (!HIST.length) return;
  const h = HIST.pop(); FUT.push({ snap: snapshot(), label: h.label });
  restore(h.snap); touch(); render(); toast("Undid: " + h.label);
}
function redo() {
  if (!FUT.length) return;
  const h = FUT.pop(); HIST.push({ snap: snapshot(), label: h.label });
  restore(h.snap); touch(); render(); toast("Redid: " + h.label);
}
function persist() { lsSet(LS_STATE, S); scheduleWrite(); }
function saveUI() { lsSet(LS_UI, { view: UI.view, current: UI.current, sort: UI.sort, filters: UI.filters, csFilter: UI.csFilter }); }
function hasContent(s) { return Object.keys(s.answers || {}).length || Object.keys(s.flags || {}).length || (s.reviewer && s.reviewer.name); }

/* ============================== shared store ============================== */
const SYNC = { mode: "local", db: null, user: null, uid: null, owner: false, ref: null, writing: false, dirty: false, timer: null, reviewers: {}, names: {}, readonly: false };
function setSync(mode) { SYNC.mode = mode; renderSync(); }
function scheduleWrite(delay) {
  if (!SYNC.ref || SYNC.readonly) return;
  SYNC.dirty = true; renderSync();
  clearTimeout(SYNC.timer);
  SYNC.timer = setTimeout(flushWrite, delay == null ? 1200 : delay);
}
async function flushWrite() {
  if (!SYNC.ref || SYNC.writing) return;
  if (!SYNC.dirty) return;
  SYNC.writing = true; SYNC.dirty = false; renderSync();
  const body = { reviewer: S.reviewer, answers: S.answers, flags: S.flags, updatedAt: S.updatedAt, bank_version: BANK.bank_version, uid: SYNC.uid };
  try {
    await SYNC.ref.set(JSON.parse(JSON.stringify(body)));
    SYNC.mode = "shared";
  } catch (e) {
    const code = e && e.code;
    if (code === "invalid_argument" || code === "not_granted" || code === "revoked") { SYNC.readonly = true; SYNC.mode = "local"; toast("Your answers are saved in this browser only. Export them when you finish."); }
    else if (code === "quota_exceeded") { SYNC.mode = "local"; toast("The shared store is full. Your answers are saved in this browser. Export them when you finish."); }
    else { SYNC.dirty = true; setTimeout(flushWrite, 3000 + Math.random() * 2000); }
  }
  SYNC.writing = false; renderSync();
  if (SYNC.dirty) scheduleWrite(400);
}
function adoptRemote(r) {
  S = normalizeState({ bank_version: r.bank_version, reviewer: r.reviewer, answers: r.answers, flags: r.flags, updatedAt: r.updatedAt });
  lsSet(LS_STATE, S);
}
async function initCapabilities() {
  const C = window.claude;
  if (!C || typeof C.use !== "function") { setSync("local"); return; }
  try { SYNC.user = await C.use("user"); } catch (e) { SYNC.user = null; }
  try { SYNC.db = await C.use("db"); } catch (e) { SYNC.db = null; }
  let canWrite = null;
  if (SYNC.user) {
    try { SYNC.owner = !!(await SYNC.user.isOwner()); } catch (e) {}
    try { SYNC.uid = await SYNC.user.id(); } catch (e) {}
    try { canWrite = await SYNC.user.can("data.write"); } catch (e) {}
  }
  if (!SYNC.db || !SYNC.uid || canWrite === false) { SYNC.readonly = canWrite === false; setSync("local"); render(); return; }
  try { SYNC.ref = SYNC.db.doc("reviews/" + SYNC.uid); } catch (e) { setSync("local"); return; }
  try {
    const snap = await SYNC.ref.get();
    if (snap.exists) {
      const r = snap.data() || {};
      if ((r.updatedAt || 0) > (S.updatedAt || 0)) { adoptRemote(r); toast("Loaded your saved answers"); }
      else if ((S.updatedAt || 0) > (r.updatedAt || 0)) scheduleWrite(0);
    } else if (hasContent(S)) scheduleWrite(0);
    SYNC.mode = "shared";
  } catch (e) { SYNC.mode = "local"; }
  try {
    SYNC.ref.onSnapshot(snap => {
      if (!snap.exists || snap.metadata.hasPendingWrites) return;
      const r = snap.data() || {};
      if ((r.updatedAt || 0) > (S.updatedAt || 0) && !SYNC.writing && !SYNC.dirty) { adoptRemote(r); render(); toast("Loaded newer answers from another device"); }
    }, () => {});
  } catch (e) {}
  if (SYNC.owner) {
    try {
      SYNC.db.collection("reviews").onSnapshot(qs => {
        const m = {}; qs.docs.forEach(d => { m[d.id] = d.data(); });
        SYNC.reviewers = m; resolveNames();
        if (UI.view === "consensus") renderView(); renderTabs();
      }, () => {});
    } catch (e) {}
  }
  render();
}
async function resolveNames() {
  if (!SYNC.user || !SYNC.user.profiles) return;
  const ids = Object.keys(SYNC.reviewers);
  if (!ids.length) return;
  try { const ps = await SYNC.user.profiles(ids); ids.forEach(id => { if (ps[id] && ps[id].name) SYNC.names[id] = ps[id].name; }); if (UI.view === "consensus") renderView(); } catch (e) {}
}

/* ============================== helpers ============================== */
const $ = s => document.querySelector(s);
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function inline(s) { return esc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>"); }
function md(s) {
  return String(s || "").split(/\n{2,}/).map(p => {
    const lines = p.split("\n");
    if (lines.every(l => /^\s*[-*] /.test(l))) return "<ul>" + lines.map(l => "<li>" + inline(l.replace(/^\s*[-*] /, "")) + "</li>").join("") + "</ul>";
    return "<p>" + lines.map(inline).join("<br>") + "</p>";
  }).join("");
}
function caseName(id) { return CASE_SHORT[id] || id; }
function statusOf(q, st) {
  st = st || S;
  const a = st.answers[q.id];
  if (a && a.committed) return a.hash && a.hash !== q.hash ? "stale" : "answered";
  if (st.flags[q.id]) return "flagged";
  if (a && a.choice) return "draft";
  if (q.resolved) return "resolved";
  if (a && (a.choice)) return "draft";
  return "open";
}
function counts(list, st) {
  const c = { total: list.length, answered: 0, flagged: 0, draft: 0, open: 0, stale: 0, resolved: 0 };
  list.forEach(q => { c[statusOf(q, st)]++; });
  return c;
}
function optLabel(q, key) {
  if (key === "other") return "Own answer";
  if (key === "abstain") return "Abstained (outside my expertise)";
  const o = q.options.find(o => o.key === key); return o ? key + ". " + o.label : key;
}
function fmtTime(t) { if (!t) return ""; const d = new Date(t); return d.toLocaleString(undefined, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }); }
function isoLocal(t) { const d = new Date(t || Date.now()); const p = n => String(n).padStart(2, "0"); return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes()); }

/* ============================== filtering ============================== */
function matches(q) {
  const f = UI.filters;
  if (f.cases.length && !f.cases.includes(q.case)) return false;
  if (f.pri !== "all" && q.priority !== f.pri) return false;
  if (f.kind !== "all" && q.kind !== f.kind) return false;
  if (f.cat !== "all" && q.category !== f.cat) return false;
  if (f.status !== "all") {
    const s = statusOf(q);
    if (f.status === "todo" && !(s === "open" || s === "draft")) return false;
    if (f.status === "flagged" && !S.flags[q.id]) return false;
    if (f.status === "answered" && !(s === "answered" || s === "stale")) return false;
    if (f.status === "resolved" && s !== "resolved") return false;
    if (f.status === "changed" && s !== "stale") return false;
  }
  if (f.q) {
    const t = f.q.toLowerCase();
    const hay = (q.id + " " + q.title + " " + q.question + " " + q.context + " " + q.category + " " + (q.related || []).join(" ")).toLowerCase();
    if (!t.split(/\s+/).every(w => hay.includes(w))) return false;
  }
  return true;
}
function sorter(a, b) {
  const co = CASE_ORDER.indexOf(a.case) - CASE_ORDER.indexOf(b.case);
  if (UI.sort === "case") return co || (PRI[a.priority] - PRI[b.priority]) || a._i - b._i;
  if (UI.sort === "category") return a.category.localeCompare(b.category) || (PRI[a.priority] - PRI[b.priority]) || co || a._i - b._i;
  return (PRI[a.priority] - PRI[b.priority]) || co || a._i - b._i;
}
function groupKey(q) { return UI.sort === "case" ? q.case : UI.sort === "category" ? q.category : q.priority; }
function groupLabel(k) { if (UI.sort === "case") return k === "ALL" ? "Cross-case and platform" : k + ". " + (CASEMAP[k] ? CASEMAP[k].title : ""); if (UI.sort === "category") return k; return PRI_LABEL[k] + " priority"; }
function filtered() { return QS.filter(matches).sort(sorter); }
function currentQ(list) {
  list = list || filtered();
  let q = UI.current && QMAP[UI.current];
  if (!q || !list.includes(q)) q = list[0] || null;
  if (q) UI.current = q.id;
  return q;
}

/* ============================== render: shell ============================== */
function render() { renderTabs(); renderProgress(); renderSync(); renderWho(); renderUndo(); renderSidebar(); renderView(); saveUI(); }
function renderTabs() {
  const tabs = [["review", "Review"], ["summary", "Progress and export"]];
  if (SYNC.owner || IMPORTS.length) tabs.push(["consensus", "Consensus"]);
  tabs.push(["guide", "Guide"]);
  if (!tabs.some(t => t[0] === UI.view)) UI.view = "review";
  $("#tabs").innerHTML = tabs.map(([k, l]) => `<button class="tab" role="tab" aria-selected="${UI.view === k}" data-view="${k}">${l}</button>`).join("");
}
function renderProgress() {
  const c = counts(QS);
  const pct = n => (100 * n / c.total).toFixed(2) + "%";
  const done = c.answered + c.stale + c.resolved;
  $("#prog").innerHTML = `<div class="bar" role="img" aria-label="${done} answered, ${c.flagged} flagged, of ${c.total}"><i class="a" style="width:${pct(done)}"></i><i class="f" style="width:${pct(c.flagged)}"></i><i class="d" style="width:${pct(c.draft)}"></i></div><span class="num">${done} of ${c.total} done${c.flagged ? ` · ${c.flagged} flagged` : ""}</span>`;
}
function renderSync() {
  const el = $("#sync"); if (!el) return;
  let cls = "local", txt = "Saved in browser";
  if (SYNC.ref && !SYNC.readonly) {
    if (SYNC.writing || SYNC.dirty) { cls = "saving"; txt = "Saving…"; }
    else if (SYNC.mode === "shared") { cls = "shared"; txt = "Saved to review"; }
  } else if (SYNC.readonly) { txt = "Browser only"; }
  el.className = "sync " + cls; el.querySelector("span").textContent = txt;
  el.title = cls === "shared" ? "Your answers are stored with this review. Only the review owner can read other reviewers' answers." : "Your answers are stored in this browser. Use Progress and export to send them.";
}
function renderWho() {
  const r = S.reviewer; $("#whoBtn").textContent = r.name ? (r.name + (r.role ? " · " + r.role : "")) : "Set your name";
}
function renderUndo() {
  const u = $("#undoBtn"), r = $("#redoBtn");
  u.disabled = !HIST.length; r.disabled = !FUT.length;
  u.title = HIST.length ? "Undo: " + HIST[HIST.length - 1].label + " (Ctrl or Cmd Z)" : "Nothing to undo";
  r.title = FUT.length ? "Redo: " + FUT[FUT.length - 1].label : "Nothing to redo";
}

/* ============================== render: sidebar ============================== */
function renderSidebar() {
  const f = UI.filters, list = filtered(), cur = UI.view === "review" ? currentQ(list) : null;
  const caseCounts = CASE_ORDER.map(id => { const l = QS.filter(q => q.case === id); return [id, l.length, counts(l)]; });
  const chip = (id, n) => `<button class="chip cc case-${id}" data-case="${id}" aria-pressed="${f.cases.includes(id)}">${caseName(id)} <span class="n">${n}</span></button>`;
  const opt = (v, cur, label) => `<option value="${v}"${cur === v ? " selected" : ""}>${label}</option>`;
  let h = `<div class="filters">
    <input class="search" id="search" type="search" placeholder="Search questions, ids, drugs…" value="${esc(f.q)}" aria-label="Search questions">
    <div class="chips" role="group" aria-label="Filter by case"><button class="chip" data-case="*" aria-pressed="${!f.cases.length}">All cases <span class="n">${QS.length}</span></button>${caseCounts.map(([id, n]) => chip(id, n)).join("")}</div>
    <div class="row2">
      <select class="sel" id="fStatus" aria-label="Filter by status">${opt("all", f.status, "Any status")}${opt("todo", f.status, "Not answered")}${opt("flagged", f.status, "Flagged")}${opt("answered", f.status, "Answered")}${opt("resolved", f.status, "Already decided")}${opt("changed", f.status, "Question changed")}</select>
      <select class="sel" id="fPri" aria-label="Filter by priority">${opt("all", f.pri, "Any priority")}${opt("high", f.pri, "High")}${opt("medium", f.pri, "Medium")}${opt("low", f.pri, "Low")}</select>
      <select class="sel" id="fKind" aria-label="Filter by type">${opt("all", f.kind, "All types")}${opt("decision", f.kind, "Decisions only")}${opt("verify", f.kind, "Checks only")}</select>
      <select class="sel" id="fCat" aria-label="Filter by category">${opt("all", f.cat, "Any category")}${CATS.map(c => opt(c, f.cat, c)).join("")}</select>
    </div>
    <div class="row2"><select class="sel" id="fSort" aria-label="Sort">${opt("priority", UI.sort, "Sort: priority first")}${opt("case", UI.sort, "Sort: by case")}${opt("category", UI.sort, "Sort: by category")}</select>
    <button class="iconbtn" id="clearF" style="justify-content:center">Clear filters</button></div>
    <div class="caseprog" aria-label="Progress by case">${caseCounts.map(([id, n, c]) => { const d = c.answered + c.stale + c.resolved; return `<div class="cp cc case-${id}" title="${id}: ${d} of ${n} answered, ${c.flagged} flagged"><b>${caseName(id)}</b><div class="bar"><i class="a" style="width:${100 * d / n}%"></i><i class="f" style="width:${100 * c.flagged / n}%"></i></div><span class="num">${d}/${n}</span></div>`; }).join("")}</div>
  </div><div class="list" id="qlist">`;
  if (!list.length) h += `<div class="empty">No questions match these filters.<br><button class="iconbtn" id="clearF2" style="margin-top:10px">Clear filters</button></div>`;
  let g = null;
  list.forEach(q => {
    const k = groupKey(q);
    if (k !== g) { g = k; const n = list.filter(x => groupKey(x) === k).length; h += `<div class="grp"><span class="lbl">${esc(groupLabel(k))}</span><span class="lbl num">${n}</span></div>`; }
    const st = statusOf(q);
    h += `<button class="qi cc case-${q.case}" data-q="${q.id}" aria-current="${cur && cur.id === q.id}"><span class="dot ${st}" title="${st}"></span><span><span class="t">${esc(q.title)}</span><span class="m"><span class="ctag">${esc(caseName(q.case))}</span>${UI.sort !== "priority" ? `<span class="pri ${q.priority}">${q.priority}</span>` : ""}${S.flags[q.id] && st !== "flagged" ? '<span style="color:var(--flag)">flagged</span>' : ""}</span></span></button>`;
  });
  h += "</div>";
  const sb = $("#sidebar"); const sc = sb.querySelector(".list") ? sb.querySelector(".list").scrollTop : 0;
  const hadFocus = document.activeElement && document.activeElement.id === "search";
  const selStart = hadFocus ? document.activeElement.selectionStart : 0;
  sb.innerHTML = h;
  const nl = sb.querySelector(".list"); if (nl) nl.scrollTop = sc;
  if (hadFocus) { const s = $("#search"); s.focus(); try { s.setSelectionRange(selStart, selStart); } catch (e) {} }
}
function scrollCurrentIntoView() { const el = document.querySelector('.qi[aria-current="true"]'); if (el) el.scrollIntoView({ block: "nearest" }); }

/* ============================== render: views ============================== */
function renderView() {
  const v = $("#view");
  if (UI.view === "summary") v.innerHTML = viewSummary();
  else if (UI.view === "consensus") v.innerHTML = viewConsensus();
  else if (UI.view === "guide") v.innerHTML = viewGuide();
  else v.innerHTML = viewQuestion();
  if (UI.view === "summary") { const ta = $("#exportText"); if (ta) ta.value = exportMarkdown(); }
  if (UI.view === "consensus") { const ta = $("#consText"); if (ta) ta.value = consensusMarkdown(); }
}

function viewQuestion() {
  const list = filtered(), q = currentQ(list);
  if (!q) return `<div class="view-inner"><div class="empty">No questions match these filters.</div></div>`;
  const a = S.answers[q.id] || {}, flagged = !!S.flags[q.id], idx = list.indexOf(q);
  const sh = q.short || { brief: [q.question], now: q.current, opts: {}, why: q.reasoning };
  const revealed = !!a.revealed, isVerify = q.kind === "verify";
  const st = statusOf(q);
  let h = `<div class="view-inner case-${q.case}">`;
  if (!S.reviewer.name) h += `<div class="banner">Add your name and role so your answers are attributed. <button class="btn" data-act="who" style="margin-left:8px;padding:4px 10px">Add my details</button></div>`;
  if (SYNC.readonly) h += `<div class="banner">Your answers save in this browser only. Send them from Progress and export.</div>`;
  h += `<div class="qhead"><span class="casebadge">${esc(caseName(q.case))}</span><span class="pribadge ${q.priority}">${PRI_LABEL[q.priority]} priority</span></div>`;
  if (q.resolved) h += `<div class="decided"><b>Decided ${esc(q.resolved.date)} by ${esc(q.resolved.by)}, applied in ${esc(q.resolved.applied_in)}.</b> ${esc(q.resolved.decision)} The text below describes the case before this decision. You can still record your own view.</div>`;
  h += `<h1 class="qtitle">${esc(q.title)}</h1>`;
  h += `<div class="situation"><ul>${sh.brief.map(x => `<li>${inline(x)}</li>`).join("")}</ul></div>`;
  h += `<div class="nowline"><span class="lbl">In the case now</span><span>${inline(sh.now)}</span></div>`;
  h += `<div class="opts" role="radiogroup" aria-label="Options">`;
  q.options.forEach(o => {
    const isRec = revealed && q.recommended === o.key;
    h += `<div class="opt" role="radio" tabindex="0" aria-checked="${a.choice === o.key}" data-choice="${o.key}">${isRec ? `<span class="rectag">${isVerify ? "Suggested" : "Claude's pick"}</span>` : ""}<span class="key">${o.key}</span><div><div class="ol">${esc(o.label)}</div>${sh.opts && sh.opts[o.key] ? `<div class="os">${inline(sh.opts[o.key])}</div>` : ""}</div></div>`;
  });
  h += `</div>`;
  h += `<div class="alts2"><button class="alt2" role="radio" aria-checked="${a.choice === "other"}" data-choice="other">Write my own answer</button><button class="alt2" role="radio" aria-checked="${a.choice === "abstain"}" data-choice="abstain">Outside my expertise</button></div>`;
  if (a.choice === "other") h += `<textarea id="otherText" placeholder="What should the case do instead, and why?" aria-label="Your own answer">${esc(a.other || "")}</textarea>`;
  const showComment = UI.commentOpen === q.id || (a.comment || "").trim();
  h += `<div class="minor"><span class="lbl">Confidence</span><div class="seg" role="group" aria-label="Confidence">${[["low", "Low"], ["moderate", "Moderate"], ["high", "High"]].map(([k, l]) => `<button data-conf="${k}" aria-pressed="${a.confidence === k}">${l}</button>`).join("")}</div>${showComment ? "" : `<button class="linkish" data-act="comment">Add a comment</button>`}</div>`;
  if (showComment) h += `<textarea id="commentText" placeholder="Reasoning, caveats, or what you checked" aria-label="Comment">${esc(a.comment || "")}</textarea>`;
  if (flagged) h += `<input class="input" id="flagNote" placeholder="Why flagged (optional)" aria-label="Why flagged" value="${esc(S.flags[q.id].note || "")}">`;
  const canCommit = a.choice && !(a.choice === "other" && !(a.other || "").trim());
  const needsRecommit = a.choice && !a.committed;
  h += `<div class="actions"><button class="btn primary" data-act="commit" ${canCommit && needsRecommit ? "" : "disabled"}>${a.committed ? "Committed" : revealed ? "Commit change" : "Commit answer"}</button>
    <button class="btn flagbtn" data-act="flag" aria-pressed="${flagged}">${flagged ? "Flagged" : "Flag for later"}</button>
    <span class="spacer"></span>
    <button class="btn" data-act="prev" ${idx <= 0 ? "disabled" : ""}>Previous</button>
    <button class="btn" data-act="next" ${idx >= list.length - 1 ? "disabled" : ""}>Next</button>
    <button class="btn" data-act="nextopen">Next<span class="long">unanswered</span><span class="short">open</span></button></div>`;
  if (st === "stale") h += `<p class="warnline">This question changed after you answered it. Review and commit again.</p>`;
  if (revealed) {
    const rec = q.options.find(o => o.key === q.recommended), first = a.firstChoice;
    let agree;
    if (a.choice === "abstain") agree = "You abstained.";
    else if (a.choice === q.recommended) agree = first && first !== a.choice ? `You changed to this from ${esc(optLabel(q, first))}. The change is recorded.` : "Your answer matches.";
    else agree = `Your answer differs${first && first !== a.choice ? `, and you first chose ${esc(optLabel(q, first))}` : ""}. A comment on why helps.`;
    h += `<section class="reveal" aria-live="polite"><span class="lbl">${isVerify ? "Suggested approach" : "Claude recommends"}</span><div class="recline"><span class="rk ${rec.key}">${rec.key}</span>${esc(rec.label)}</div><p class="why">${inline(sh.why)}</p><div class="agree">${agree}</div></section>`;
  } else {
    h += `<div class="locked">Claude's ${isVerify ? "suggestion" : "recommendation"} appears after you commit.</div>`;
  }
  // everything long lives here, collapsed
  h += `<details class="fold full" id="fullDetail"${UI.fullOpen ? " open" : ""}><summary><span class="lbl">Full detail</span></summary><div class="inner">`;
  h += `<div class="sect"><span class="lbl">Context</span><div class="prose">${md(q.context)}</div></div>`;
  if (q.current) h += `<div class="sect"><span class="lbl">What the case file does now</span><div class="now">${inline(q.current)}</div></div>`;
  if ((q.quotes || []).length) h += `<div class="sect"><span class="lbl">Sources, verbatim</span><div class="quotes">${q.quotes.map(x => `<blockquote>${inline(x.text)}<cite>${esc(x.source)}</cite></blockquote>`).join("")}</div></div>`;
  h += `<div class="sect"><span class="lbl">Options in full</span>${q.options.map(o => `<div class="optfull" data-k="${o.key}"><b>${o.key}. ${esc(o.label)}</b><span>${inline(o.detail)}</span><span class="muted">${inline(o.tradeoff)}</span><span class="mono">${esc(o.implementation)}</span></div>`).join("")}</div>`;
  if (revealed) h += `<div class="sect"><span class="lbl">Full reasoning</span><div class="prose">${md(q.reasoning)}</div>${q.evidence ? `<p class="note">Evidence: ${inline(q.evidence)}</p>` : ""}</div>`;
  h += `</div></details></div>`;
  return h;
}

/* ============================== actions ============================== */
function ans(qid) { if (!S.answers[qid]) S.answers[qid] = { choice: null, other: "", comment: "", confidence: null, committed: false }; return S.answers[qid]; }
function choose(key) {
  const q = currentQ(); if (!q) return;
  const a = S.answers[q.id];
  if (a && a.choice === key) return;
  mutate(`chose ${key === "other" ? "own answer" : key === "abstain" ? "abstain" : key} on ${q.id}`, () => {
    const x = ans(q.id); x.choice = key; x.committed = false;
  });
  if (key === "other") setTimeout(() => { const t = $("#otherText"); if (t) t.focus(); }, 0);
}
function commit() {
  const q = currentQ(); if (!q) return;
  const a = S.answers[q.id];
  if (!a || !a.choice || a.committed) return;
  if (a.choice === "other" && !(a.other || "").trim()) { toast("Write your own answer before committing it"); const t = $("#otherText"); if (t) t.focus(); return; }
  mutate(`committed ${q.id}`, () => {
    const x = ans(q.id);
    if (!x.revealed) { x.firstChoice = x.choice; x.revealed = true; x.revealedAt = Date.now(); }
    x.changedAfterReveal = x.firstChoice !== x.choice;
    x.committed = true; x.committedAt = Date.now(); x.hash = q.hash;
    if (S.flags[q.id] && !S.flags[q.id].note) delete S.flags[q.id];
  });
  const r = document.querySelector(".reveal"); if (r) r.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "nearest" });
}
function toggleFlag() {
  const q = currentQ(); if (!q) return;
  const on = !!S.flags[q.id];
  mutate(on ? `unflagged ${q.id}` : `flagged ${q.id}`, () => { if (on) delete S.flags[q.id]; else S.flags[q.id] = { note: "", at: Date.now() }; });
  toast(on ? "Flag removed" : "Flagged for later. It stays unanswered until you come back.", true);
}
function setConf(k) {
  const q = currentQ(); if (!q) return;
  const cur = S.answers[q.id] && S.answers[q.id].confidence;
  mutate(`confidence on ${q.id}`, () => { ans(q.id).confidence = cur === k ? null : k; });
}
function go(delta) {
  const list = filtered(), q = currentQ(list); if (!q) return;
  const i = list.indexOf(q) + delta; if (i < 0 || i >= list.length) return;
  openQ(list[i].id);
}
function nextOpen() {
  const list = filtered(); const q = currentQ(list);
  const start = q ? list.indexOf(q) : -1;
  const order = list.slice(start + 1).concat(list.slice(0, start + 1));
  const nx = order.find(x => { const s = statusOf(x); return (s === "open" || s === "draft") && x.id !== (q && q.id); });
  if (nx) openQ(nx.id); else toast(list.length ? "Every question in this view is answered or flagged" : "No questions in this view");
}
function openQ(id) {
  UI.current = id; UI.view = "review";
  $("#sidebar").classList.remove("open");
  render(); $("#view").scrollTop = 0; scrollCurrentIntoView();
}
// text fields: one undo step per editing session
let editSnap = null;
function textStart(label) { if (!editSnap) { editSnap = true; pushHist(label); renderUndo(); } }
function textEnd() { editSnap = null; }
let textTimer = null;
function textChanged(fn) { fn(); S.updatedAt = Date.now(); updateCommitButton(); clearTimeout(textTimer); textTimer = setTimeout(() => { persist(); renderProgress(); renderSidebar(); updateCommitButton(); }, 350); lsSet(LS_STATE, S); }
function updateCommitButton() {
  const q = currentQ(); if (!q) return; const a = S.answers[q.id] || {};
  const b = document.querySelector('[data-act="commit"]'); if (!b) return;
  const can = a.choice && !(a.choice === "other" && !(a.other || "").trim()) && !a.committed;
  b.disabled = !can;
}

/* ============================== export ============================== */
function answeredRecords(st) {
  return QS.filter(q => st.answers[q.id] && st.answers[q.id].committed).map(q => ({ q, a: st.answers[q.id] }));
}
function exportMarkdown(st) {
  st = st || S;
  const r = st.reviewer || {};
  const recs = answeredRecords(st);
  const flags = QS.filter(q => st.flags[q.id] && !(st.answers[q.id] && st.answers[q.id].committed));
  const open = QS.filter(q => !(st.answers[q.id] && st.answers[q.id].committed) && !st.flags[q.id]);
  const changed = recs.filter(x => x.a.changedAfterReveal).length;
  const L = [];
  L.push("# EMSim physician review: answers to apply");
  L.push("");
  L.push(`Reviewer: ${r.name || "(name not given)"}${r.role ? ", " + r.role : ""}`);
  if (r.disclosures) L.push(`Disclosures: ${r.disclosures}`);
  L.push(`Question bank: ${BANK.bank_version}. Exported ${isoLocal()}.`);
  L.push(`Answered ${recs.length} of ${QS.length}. Flagged for later ${flags.length}. Not yet answered ${open.length}. Answers changed after seeing Claude's recommendation: ${changed}.`);
  L.push("Case packs the questions were written against (case JSON SHA-256, first 12): " + BANK.cases.filter(c => c.case_json_sha256).map(c => c.id + " " + c.case_json_sha256.slice(0, 12)).join(", ") + ".");
  L.push("");
  L.push("## Instructions for Claude");
  L.push("");
  L.push("1. Work in the EMSIM1 repository. Load `cases/review/physician-review-bank.json` and check that its bank_version matches the one above and that each item's hash below matches the bank. If a hash differs, the question changed after the reviewer answered it: list it and ask before applying.");
  L.push("2. Check each case JSON against the SHA-256 prefixes above. If a case changed since the bank was written, re-verify each item's \"What the case does now\" before editing.");
  L.push("3. For each decision, apply the chosen option's implementation. For an own answer, implement the reviewer's words and ask where they are ambiguous. Change nothing for abstentions, flagged items or unanswered items.");
  L.push("4. For checks, \"Ask Claude to pre-check first\" means run the described pre-check and report the findings back for the reviewer to confirm. It is not a sign-off.");
  L.push("5. After editing, rerun the toolchain for each affected case: bind_catalog.py, validate_case.py, build_simulator.py, engine-tests.js with the case tests, sim_runner.py and validator-tests.py.");
  L.push("6. Record the review in each affected `<CASE>-review-packet.md` under a new section \"Physician review\": item id, decision, reviewer, date, confidence, comment, and whether the answer changed after the recommendation was shown. Tick the matching section 14.3 checklist lines only for items this reviewer signed. Regenerate each `<CASE>-review-matrix.md` and note the review at its top.");
  L.push("7. An answer that changed after the recommendation was shown is not independent agreement. Say so wherever the review is summarized.");
  L.push("8. If several reviewers' exports are applied together, do not apply an item where they disagree. List it for resolution.");
  L.push("");
  CASE_ORDER.forEach(cid => {
    const rs = recs.filter(x => x.q.case === cid);
    if (!rs.length) return;
    L.push(`## ${cid === "ALL" ? "Cross-case and platform" : cid + ": " + (CASEMAP[cid] ? CASEMAP[cid].title : "")} (${rs.length})`);
    L.push("");
    rs.forEach(({ q, a }) => {
      L.push(`### ${q.id}. ${q.title}`);
      L.push(`Priority ${q.priority}, ${q.kind === "verify" ? "check" : "decision"}, hash ${q.hash}${a.hash && a.hash !== q.hash ? " (ANSWERED AGAINST AN EARLIER VERSION " + a.hash + ")" : ""}`);
      L.push(`- Answer: ${optLabel(q, a.choice)}`);
      if (a.choice === "other") L.push(`- Reviewer's own answer: ${(a.other || "").trim().replace(/\n+/g, " ")}`);
      const o = q.options.find(o => o.key === a.choice);
      if (o) L.push(`- Implementation: ${o.implementation}`);
      L.push(`- Claude had recommended: ${q.recommended}${a.choice === q.recommended ? " (same)" : ""}`);
      if (a.changedAfterReveal) L.push(`- Changed after seeing the recommendation. First answer: ${optLabel(q, a.firstChoice)}`);
      if (a.confidence) L.push(`- Confidence: ${a.confidence}`);
      if ((a.comment || "").trim()) L.push(`- Comment: ${a.comment.trim().replace(/\n+/g, " ")}`);
      L.push(`- Committed: ${isoLocal(a.committedAt)}`);
      L.push("");
    });
  });
  if (flags.length) {
    L.push(`## Flagged for later, do not apply (${flags.length})`);
    L.push("");
    flags.forEach(q => { const n = (st.flags[q.id].note || "").trim(); L.push(`- ${q.id}. ${q.title}${n ? " Note: " + n : ""}`); });
    L.push("");
  }
  if (open.length) {
    L.push(`## Not yet answered (${open.length})`);
    L.push("");
    L.push(open.map(q => q.id).join(", "));
    L.push("");
  }
  L.push("## Machine-readable record");
  L.push("");
  L.push("```json");
  L.push(JSON.stringify(recordJSON(st)));
  L.push("```");
  return L.join("\n");
}
function recordJSON(st) {
  return {
    kind: "emsim-physician-review", bank_version: BANK.bank_version, exported: new Date().toISOString(), reviewer: st.reviewer,
    answers: answeredRecords(st).map(({ q, a }) => ({ id: q.id, hash: a.hash || q.hash, choice: a.choice, other: a.other || "", confidence: a.confidence || null, comment: a.comment || "", first_choice: a.firstChoice || a.choice, changed_after_reveal: !!a.changedAfterReveal, recommended: q.recommended, committed_at: a.committedAt || null })),
    flags: Object.keys(st.flags).map(id => ({ id, note: st.flags[id].note || "" }))
  };
}
function backupJSON() { return JSON.stringify({ kind: "emsim-physician-review-backup", bank_version: BANK.bank_version, state: S }, null, 1); }
async function copyText(text, okMsg) {
  try { await navigator.clipboard.writeText(text); toast(okMsg || "Copied"); return true; }
  catch (e) { toast("Copy was blocked here. The text is selected: press Ctrl or Cmd C."); return false; }
}
async function saveFile(filename, data) {
  const C = window.claude; let dl = null;
  try { dl = C && C.use ? await C.use("downloads") : null; } catch (e) {}
  if (!dl) { toast("Downloads are not available in this view. Use Copy instead."); return; }
  try { await dl.save({ filename, data }); toast("Saved " + filename); }
  catch (e) { if (e && e.code === "declined") toast("Download cancelled"); else toast("The download did not start. Use Copy instead."); }
}
function parseRecord(text) {
  text = String(text || "").trim();
  const m = text.match(/```json\s*([\s\S]*?)```/);
  const raw = m ? m[1] : text;
  const o = JSON.parse(raw);
  if (o.kind === "emsim-physician-review-backup" && o.state) return normalizeState(o.state);
  if (o.kind === "emsim-physician-review") {
    const st = blankState(); st.reviewer = Object.assign(st.reviewer, o.reviewer || {});
    (o.answers || []).forEach(a => { st.answers[a.id] = { choice: a.choice, other: a.other, confidence: a.confidence, comment: a.comment, firstChoice: a.first_choice, changedAfterReveal: a.changed_after_reveal, committed: true, revealed: true, committedAt: a.committed_at, hash: a.hash }; });
    (o.flags || []).forEach(f => { st.flags[f.id] = { note: f.note || "" }; });
    st.updatedAt = Date.parse(o.exported) || Date.now(); return st;
  }
  if (o.answers && o.flags) return normalizeState(o);
  throw new Error("not a review record");
}

/* ============================== summary view ============================== */
function viewSummary() {
  const c = counts(QS), recs = answeredRecords(S);
  const dec = recs.filter(x => x.q.kind === "decision" && x.a.choice !== "abstain" && x.a.choice !== "other");
  const same = dec.filter(x => x.a.choice === x.q.recommended).length;
  const firstSame = dec.filter(x => (x.a.firstChoice || x.a.choice) === x.q.recommended).length;
  const changed = recs.filter(x => x.a.changedAfterReveal).length;
  const highOpen = QS.filter(q => q.priority === "high" && !(S.answers[q.id] && S.answers[q.id].committed)).length;
  let h = `<div class="view-inner"><div class="sect"><h1 class="qtitle">Progress and export</h1><p class="lead">Your progress, the questions you flagged, and the text to paste back into Claude when you are done. You can export at any point and export again later.</p></div>`;
  h += `<div class="stats"><div class="stat"><b>${c.answered + c.stale}</b><span>answered of ${c.total}</span></div><div class="stat"><b>${c.flagged}</b><span>flagged for later</span></div><div class="stat"><b>${highOpen}</b><span>high priority still open</span></div><div class="stat"><b>${changed}</b><span>changed after the reveal</span></div><div class="stat"><b>${dec.length ? Math.round(100 * firstSame / dec.length) + "%" : "–"}</b><span>first answers matching Claude (${dec.length} decisions)</span></div></div>`;
  if (dec.length && same !== firstSame) h += `<p class="note">After seeing the recommendation, agreement moved from ${firstSame} to ${same} of ${dec.length}. The export records each change so it is not counted as independent agreement.</p>`;
  h += `<div class="tablewrap"><table><thead><tr><th>Case</th><th class="num">Questions</th><th class="num">Answered</th><th class="num">Flagged</th><th class="num">High priority open</th><th></th></tr></thead><tbody>`;
  CASE_ORDER.forEach(id => {
    const l = QS.filter(q => q.case === id), k = counts(l), ho = l.filter(q => q.priority === "high" && !(S.answers[q.id] && S.answers[q.id].committed)).length;
    h += `<tr><td class="case-${id}"><span class="ctag">${caseName(id)}</span> <span class="muted">${esc(CASEMAP[id] ? CASEMAP[id].title : "")}</span></td><td class="num">${l.length}</td><td class="num">${k.answered + k.stale}</td><td class="num">${k.flagged}</td><td class="num">${ho}</td><td><button class="linkbtn" data-filtercase="${id}">Review</button></td></tr>`;
  });
  h += `</tbody></table></div>`;
  const fl = QS.filter(q => S.flags[q.id]);
  h += `<section class="sect"><span class="lbl">Flagged for later (${fl.length})</span>`;
  if (!fl.length) h += `<p class="note">Nothing flagged. Use Flag for later on any question you want to leave open and come back to.</p>`;
  else h += `<div class="tablewrap"><table><tbody>${fl.map(q => `<tr><td style="width:90px"><button class="linkbtn" data-jump="${q.id}">${q.id}</button></td><td>${esc(q.title)}${S.flags[q.id].note ? `<div class="note">${esc(S.flags[q.id].note)}</div>` : ""}</td><td class="num">${S.answers[q.id] && S.answers[q.id].committed ? "answered" : ""}</td></tr>`).join("")}</tbody></table></div>`;
  h += `</section>`;
  const stale = QS.filter(q => statusOf(q) === "stale");
  if (stale.length) h += `<div class="banner">${stale.length} question${stale.length > 1 ? "s" : ""} changed after you answered: ${stale.map(q => `<button class="linkbtn" data-jump="${q.id}">${q.id}</button>`).join(", ")}. Review and commit again.</div>`;
  h += `<section class="sect"><span class="lbl">Paste-back text for Claude</span><p class="note">Copy this and paste it into the EMSim project in Claude. It lists each answer with the file change it implies, what stays open, and instructions for applying the review and recording it in the packets and matrices.</p><textarea class="exportbox" id="exportText" readonly aria-label="Export text"></textarea><div class="btnrow"><button class="btn primary" data-act="copyExport">Copy text</button><button class="btn" data-act="dlExport">Download .md</button><span class="spacer"></span><button class="btn" data-act="dlBackup">Download backup</button><label class="btn" style="cursor:pointer">Restore backup<input type="file" id="restoreFile" accept=".json,.md,.txt,application/json" hidden></label></div></section>`;
  h += `<section class="sect"><span class="lbl">Start over</span><div class="btnrow" id="resetRow"><button class="btn danger" data-act="reset1">Clear all my answers</button></div></section>`;
  h += `</div>`;
  return h;
}

/* ============================== consensus view ============================== */
function allReviews() {
  const out = [];
  Object.entries(SYNC.reviewers).forEach(([id, r]) => { const st = normalizeState(r); out.push({ key: "u:" + id, name: (st.reviewer.name || SYNC.names[id] || "Reviewer") , role: st.reviewer.role || "", st, src: "shared", isMe: id === SYNC.uid }); });
  if (!Object.keys(SYNC.reviewers).length || !SYNC.uid || !SYNC.reviewers[SYNC.uid]) { if (hasContent(S)) out.push({ key: "me", name: S.reviewer.name || "You", role: S.reviewer.role, st: S, src: "this browser", isMe: true }); }
  IMPORTS.forEach((im, i) => { const st = normalizeState(im.state); out.push({ key: "i:" + i, name: st.reviewer.name || "Imported reviewer " + (i + 1), role: st.reviewer.role || "", st, src: "imported", idx: i }); });
  return out;
}
function tally(q, revs) {
  const t = { A: 0, B: 0, C: 0, other: 0, abstain: 0, n: 0, items: [] };
  revs.forEach(r => { const a = r.st.answers[q.id]; if (a && a.committed) { t[a.choice] = (t[a.choice] || 0) + 1; if (a.choice !== "abstain") t.n++; t.items.push({ r, a }); } });
  const vals = ["A", "B", "C"].map(k => t[k]).concat([t.other]);
  t.top = Math.max(...vals);
  t.split = t.n >= 2 && (t.top < t.n || t.other > 0);
  t.unanimous = t.n >= 2 && !t.split;
  t.flaggedBy = revs.filter(r => r.st.flags[q.id]).map(r => r.name);
  return t;
}
function viewConsensus() {
  const revs = allReviews();
  let h = `<div class="view-inner"><div class="sect"><h1 class="qtitle">Consensus</h1><p class="lead">Every reviewer's answers side by side. Only you can see this tab. Reviewers see only their own answers.</p></div>`;
  h += `<section class="sect"><span class="lbl">Reviewers (${revs.length})</span>`;
  if (!revs.length) h += `<p class="note">No answers yet. Share this page and invite each physician by email as an Editor so their answers save here. A reviewer who can only view the page can send you their exported text, which you can import below.</p>`;
  else h += `<div class="tablewrap"><table><thead><tr><th>Reviewer</th><th>Source</th><th class="num">Answered</th><th class="num">Flagged</th><th class="num">Changed after reveal</th><th>Last change</th><th></th></tr></thead><tbody>${revs.map(r => { const k = counts(QS, r.st); const ch = answeredRecords(r.st).filter(x => x.a.changedAfterReveal).length; return `<tr><td><b>${esc(r.name)}</b>${r.role ? ` <span class="muted">${esc(r.role)}</span>` : ""}${r.isMe ? ' <span class="muted">(you)</span>' : ""}</td><td>${r.src}</td><td class="num">${k.answered + k.stale}</td><td class="num">${k.flagged}</td><td class="num">${ch}</td><td>${esc(fmtTime(r.st.updatedAt))}</td><td>${r.src === "imported" ? `<button class="linkbtn" data-rmimport="${r.idx}">Remove</button>` : ""}</td></tr>`; }).join("")}</tbody></table></div>`;
  h += `<details class="fold"><summary><span class="lbl">Import a reviewer's export</span></summary><div class="sect" style="margin-top:10px"><p class="note">Paste the full text a reviewer exported (or their backup file). It stays in this browser and is added to the table above.</p><textarea id="importText" placeholder="Paste exported text here"></textarea><div class="btnrow"><button class="btn" data-act="doImport">Import</button><label class="btn" style="cursor:pointer">Import a file<input type="file" id="importFile" accept=".json,.md,.txt" hidden></label></div></div></details></section>`;
  if (revs.length) {
    const rows = QS.map(q => ({ q, t: tally(q, revs) }));
    const nSplit = rows.filter(x => x.t.split).length, nUn = rows.filter(x => x.t.unanimous).length, nAny = rows.filter(x => x.t.items.length).length;
    h += `<div class="stats"><div class="stat"><b>${nAny}</b><span>questions with any answer</span></div><div class="stat"><b>${nUn}</b><span>unanimous (2 or more)</span></div><div class="stat"><b>${nSplit}</b><span>split, need resolution</span></div><div class="stat"><b>${rows.filter(x => x.t.flaggedBy.length).length}</b><span>flagged by someone</span></div></div>`;
    const f = UI.csFilter;
    const fbtn = (k, l) => `<button class="chip" data-csf="${k}" aria-pressed="${f === k}">${l}</button>`;
    h += `<div class="btnrow">${fbtn("all", "All answered")}${fbtn("split", "Splits")}${fbtn("unanimous", "Unanimous")}${fbtn("comments", "With comments")}${fbtn("flagged", "Flagged")}${fbtn("differs", "Differs from Claude")}<span class="spacer"></span><span class="legend"><span><i class="cA"></i>A</span><span><i class="cB"></i>B</span><span><i class="cC"></i>C</span><span><i class="cO"></i>Own</span><span><i class="cX"></i>Abstain</span></span></div>`;
    const shown = rows.filter(({ q, t }) => {
      if (f === "split") return t.split;
      if (f === "unanimous") return t.unanimous;
      if (f === "comments") return t.items.some(x => (x.a.comment || "").trim() || x.a.choice === "other");
      if (f === "flagged") return t.flaggedBy.length > 0;
      if (f === "differs") return t.items.some(x => x.a.choice !== "abstain" && x.a.choice !== q.recommended);
      return t.items.length > 0;
    });
    h += `<div class="tablewrap">${shown.length ? shown.map(({ q, t }) => {
      const tot = t.items.length || 1, seg = k => `<i class="c${k === "other" ? "O" : k === "abstain" ? "X" : k}" style="width:${100 * (t[k] || 0) / tot}%"></i>`;
      return `<div class="crow"><div class="top"><button class="linkbtn" data-jump="${q.id}">${q.id}</button><span class="ttl">${esc(q.title)}</span>${t.split ? '<span class="split">Split</span>' : t.unanimous ? '<span class="unan">Unanimous</span>' : ""}<span class="dist" title="A ${t.A}, B ${t.B}, C ${t.C}, own ${t.other}, abstain ${t.abstain}">${["A", "B", "C", "other", "abstain"].map(seg).join("")}</span><span class="note">Claude: ${q.recommended}</span></div><div class="rv">${t.items.map(({ r, a }) => `<span class="rvc" title="${esc((a.comment || "") + (a.choice === "other" ? " Own answer: " + (a.other || "") : ""))}">${esc(r.name)}: <b>${a.choice === "other" ? "own" : a.choice === "abstain" ? "abstain" : a.choice}</b>${a.confidence ? " · " + a.confidence[0] : ""}${a.changedAfterReveal ? " · changed" : ""}${(a.comment || "").trim() ? " · comment" : ""}</span>`).join("")}${t.flaggedBy.length ? `<span class="rvc" style="color:var(--flag)">flagged: ${esc(t.flaggedBy.join(", "))}</span>` : ""}</div>${t.items.filter(x => (x.a.comment || "").trim() || x.a.choice === "other").map(({ r, a }) => `<div class="note"><b>${esc(r.name)}</b>: ${a.choice === "other" ? "Own answer: " + esc(a.other) + " " : ""}${esc(a.comment || "")}</div>`).join("")}</div>`;
    }).join("") : '<div class="empty">Nothing matches this filter.</div>'}</div>`;
    h += `<section class="sect"><span class="lbl">Paste-back text for all reviewers</span><p class="note">Unanimous items are listed to apply. Split items are listed for resolution and must not be applied until you decide.</p><textarea class="exportbox" id="consText" readonly></textarea><div class="btnrow"><button class="btn primary" data-act="copyCons">Copy text</button><button class="btn" data-act="dlCons">Download .md</button></div></section>`;
  }
  h += `</div>`;
  return h;
}
function consensusMarkdown() {
  const revs = allReviews(); const L = [];
  L.push("# EMSim physician review: consensus of " + revs.length + " reviewer" + (revs.length === 1 ? "" : "s"));
  L.push("");
  L.push(`Question bank: ${BANK.bank_version}. Exported ${isoLocal()}.`);
  L.push("Reviewers: " + revs.map(r => r.name + (r.role ? " (" + r.role + ")" : "")).join(", ") + ".");
  L.push("");
  L.push("## Instructions for Claude");
  L.push("");
  L.push("1. Follow the same rules as a single-reviewer export: check bank_version and each hash against `cases/review/physician-review-bank.json`, re-verify against the case JSON if its SHA-256 changed, rerun the toolchain after edits, and record every applied item in the case's review packet under \"Physician review\" with each reviewer's answer and comment.");
  L.push("2. Apply items under \"Agreed\" only. An item is agreed when every reviewer who answered chose the same lettered option (abstentions ignored) and at least two answered, or when only one reviewer answered and the owner accepts single-reviewer sign-off.");
  L.push("3. Do not apply items under \"Split\" or \"Own answers\". List them back to the owner for resolution.");
  L.push("");
  const rows = QS.map(q => ({ q, t: tally(q, revs) })).filter(x => x.t.items.length);
  const agreed = rows.filter(x => !x.t.split && x.t.n >= 1 && x.t.items.some(i => ["A", "B", "C"].includes(i.a.choice)));
  const split = rows.filter(x => x.t.split);
  const sec = (title, list) => {
    L.push(`## ${title} (${list.length})`); L.push("");
    list.forEach(({ q, t }) => {
      const choice = ["A", "B", "C"].find(k => t[k] === t.top && t.top > 0);
      L.push(`### ${q.id}. ${q.title}`);
      L.push(`Hash ${q.hash}. Claude had recommended ${q.recommended}. ${t.n} answered${t.n === 1 ? " (single reviewer)" : ""}.`);
      if (title.startsWith("Agreed") && choice) { const o = q.options.find(o => o.key === choice); L.push(`- Decision: ${choice}. ${o.label}`); L.push(`- Implementation: ${o.implementation}`); }
      t.items.forEach(({ r, a }) => L.push(`- ${r.name}: ${optLabel(q, a.choice)}${a.confidence ? ", confidence " + a.confidence : ""}${a.changedAfterReveal ? ", changed after reveal from " + a.firstChoice : ""}${a.choice === "other" ? ". Own answer: " + (a.other || "").replace(/\n+/g, " ") : ""}${(a.comment || "").trim() ? ". Comment: " + a.comment.trim().replace(/\n+/g, " ") : ""}`));
      if (t.flaggedBy.length) L.push(`- Flagged by: ${t.flaggedBy.join(", ")}`);
      L.push("");
    });
  };
  sec("Agreed", agreed);
  sec("Split, do not apply", split);
  const none = QS.filter(q => !rows.find(x => x.q === q));
  if (none.length) { L.push(`## No answers yet (${none.length})`); L.push(""); L.push(none.map(q => q.id).join(", ")); L.push(""); }
  return L.join("\n");
}

/* ============================== guide view ============================== */
function viewGuide() {
  let h = `<div class="view-inner guide"><div class="sect"><h1 class="qtitle">How this review works</h1><p class="lead">Question bank ${esc(BANK.bank_version)}. ${QS.length} questions cover every open clinical decision in the four EMSim cases, plus cross-case questions about scoring, timing and the shared catalog. Each question gives you the context from the case, what the case does now, verbatim quotes from the sources, and three options. Claude's recommendation stays hidden until you commit.</p></div>`;
  h += `<section class="card sect"><h2>Before you start</h2><ol>
  <li>Play each case you are reviewing once, cold, before reading its questions. The questions cannot then shape your first impression.</li>
  <li>The questions, context and options were written by the same AI model that drafted much of the content under review. Read them critically. If a question seems framed to favor one option, say so in the comment or choose Write my own answer.</li>
  <li>Answer independently. You will not see other reviewers' answers. The review owner sees all answers side by side.</li>
  <li>Use Outside my expertise freely. An abstention is better than a guess, and it changes nothing in the case.</li>
  <li>Use Flag for later for anything you want to check or discuss. Flagged questions stay unanswered and are never applied.</li>
  <li>High priority questions could teach something clinically wrong, or they depart from the physician-written seed. If time is short, filter to High and do those first.</li></ol></section>`;
  h += `<section class="card sect"><h2>What the labels mean</h2><ul>
  <li>Each case has one color. <b>High priority</b> questions could teach something clinically wrong or depart from the physician-written seed.</li>
  <li><b>In the case now</b> was checked against the current case file. Several review packets are older than the case files, so where they disagree the question follows the case file.</li>
  <li>Full detail, under each question, holds the complete context, verbatim sources, each option's trade-off and the exact file change Claude would make.</li>
  <li>Nurse prompt times quoted in questions are Easy-mode figures unless the question says otherwise. Normal mode, the default, triples prompt deadlines but not deterioration deadlines. ALL-02 asks about this.</li></ul></section>`;
  h += `<section class="card sect"><h2>Keyboard</h2><div class="kbdgrid"><kbd>A</kbd><span>choose option A (also B, C)</span><kbd>O</kbd><span>write my own answer</span><kbd>X</kbd><span>outside my expertise</span><kbd>Enter</kbd><span>commit the answer</span><kbd>F</kbd><span>flag for later</span><kbd>J</kbd> <span>next question (K previous, N next unanswered)</span><kbd>/</kbd><span>search</span><kbd>Ctrl Z</kbd><span>undo (Shift for redo, Cmd on a Mac)</span></div></section>`;
  h += `<section class="card sect"><h2>Saving and sending your answers</h2><p>Every change saves as you go. If you were invited as an Editor, your answers are stored with this review under your account, and the owner can read them. Otherwise they stay in this browser. Either way, Progress and export produces the text to paste back into Claude, and a backup file you can restore on another device.</p></section>`;
  if ((BANK.protocol_notes || []).length) h += `<details class="fold card"><summary><span class="lbl">Review protocol, suggested (${BANK.protocol_notes.length} notes)</span></summary><div class="prose" style="margin-top:10px"><ul>${BANK.protocol_notes.map(n => `<li>${inline(n)}</li>`).join("")}</ul></div></details>`;
  BANK.cases.forEach(c => {
    h += `<details class="fold card"><summary><span class="lbl">${c.id}</span><span style="font-weight:600">${esc(c.title)}</span></summary><div class="prose" style="margin-top:10px">${md(c.summary)}`;
    if ((c.stale_packet_findings || []).length) h += `<p><b>Where the review packet no longer matches the case (${c.stale_packet_findings.length})</b></p><ul>${c.stale_packet_findings.map(s => `<li>${inline(s)}</li>`).join("")}</ul>`;
    h += `</div></details>`;
  });
  h += `<details class="fold card"><summary><span class="lbl">How the question bank was built</span></summary><div class="prose" style="margin-top:10px"><p>${esc(BANK.generated_by)} ${esc(BANK.sources_note)}</p><ul>${(BANK.merge_log || []).map(n => `<li>${esc(n)}</li>`).join("")}</ul></div></details>`;
  h += `</div>`;
  return h;
}

/* ============================== modal & toast ============================== */
function openWho(first) {
  const r = S.reviewer;
  $("#modal").innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="whoT"><form class="box" id="whoForm"><h2 id="whoT">${first ? "EMSim physician review" : "Your reviewer details"}</h2>${first ? `<p class="muted">You will review ${QS.length} open decisions across four simulation cases, one at a time. Your progress saves as you go, and you can stop and come back.</p>` : ""}<label>Your name, as it should appear in the sign-off record<input class="input" id="whoName" required value="${esc(r.name)}" placeholder="Dr Jane Smith"></label><label>Role and specialty<input class="input" id="whoRole" value="${esc(r.role)}" placeholder="EM attending, medical toxicology"></label><label>Disclosures (optional)<input class="input" id="whoDisc" value="${esc(r.disclosures)}" placeholder="Relationships to the product or to vendors of drugs or devices in the cases"></label><div class="btnrow" style="justify-content:flex-end">${first ? `<button type="button" class="btn" data-act="guide">Read the guide first</button>` : `<button type="button" class="btn" data-act="closeModal">Cancel</button>`}<button type="submit" class="btn primary">${first ? "Start reviewing" : "Save"}</button></div></form></div>`;
  setTimeout(() => { const n = $("#whoName"); if (n) n.focus(); }, 0);
}
function closeModal() { $("#modal").innerHTML = ""; }
let toastTimer = null;
function toast(msg, withUndo) {
  $("#toastHost").innerHTML = `<div class="toast" role="status"><span>${esc(msg)}</span>${withUndo && HIST.length ? '<button data-act="undo">Undo</button>' : ""}</div>`;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { $("#toastHost").innerHTML = ""; }, 3800);
}

/* ============================== events ============================== */
document.addEventListener("click", e => {
  const t = e.target.closest("button,[data-choice],[data-q],summary");
  if (!t) return;
  if (t.tagName === "SUMMARY") return;
  if (t.closest("details.impl") && !t.dataset.choice) return;
  const d = t.dataset;
  if (d.view) { UI.view = d.view; render(); $("#view").scrollTop = 0; return; }
  if (d.q) { openQ(d.q); return; }
  if (d.jump) { if (!matches(QMAP[d.jump])) { UI.filters = { cases: [], pri: "all", status: "all", kind: "all", cat: "all", q: "" }; } openQ(d.jump); return; }
  if (d.choice) { if (e.target.closest("details.impl")) return; choose(d.choice); return; }
  if (d.conf) { setConf(d.conf); return; }
  if (d.case) {
    const f = UI.filters;
    if (d.case === "*") f.cases = [];
    else if (e.shiftKey || e.metaKey || e.ctrlKey) f.cases = f.cases.includes(d.case) ? f.cases.filter(x => x !== d.case) : f.cases.concat(d.case);
    else f.cases = (f.cases.length === 1 && f.cases[0] === d.case) ? [] : [d.case];
    render(); return;
  }
  if (d.filtercase) { UI.filters.cases = [d.filtercase]; UI.view = "review"; UI.current = null; render(); return; }
  if (d.csf) { UI.csFilter = d.csf; renderView(); saveUI(); return; }
  if (d.rmimport != null && d.rmimport !== "") { IMPORTS.splice(+d.rmimport, 1); lsSet(LS_IMPORTS, IMPORTS); render(); return; }
  switch (d.act) {
    case "commit": commit(); break;
    case "comment": UI.commentOpen = currentQ() && currentQ().id; renderView(); setTimeout(() => { const t = $("#commentText"); if (t) t.focus(); }, 0); break;
    case "flag": toggleFlag(); break;
    case "prev": go(-1); break;
    case "next": go(1); break;
    case "nextopen": nextOpen(); break;
    case "undo": undo(); break;
    case "who": openWho(false); break;
    case "closeModal": closeModal(); break;
    case "guide": { const n = $("#whoName"); if (n && n.value.trim()) { mutate("set reviewer details", () => { S.reviewer.name = n.value.trim(); S.reviewer.role = $("#whoRole").value.trim(); S.reviewer.disclosures = $("#whoDisc").value.trim(); }, { render: false }); } closeModal(); UI.view = "guide"; render(); break; }
    case "copyExport": { const ta = $("#exportText"); ta.value = exportMarkdown(); ta.select(); copyText(ta.value, "Copied. Paste it into the EMSim project in Claude."); break; }
    case "dlExport": saveFile(`emsim-review-${(S.reviewer.name || "reviewer").replace(/[^A-Za-z0-9]+/g, "-")}-${isoLocal().slice(0, 10)}.md`, exportMarkdown()); break;
    case "dlBackup": saveFile(`emsim-review-backup-${(S.reviewer.name || "reviewer").replace(/[^A-Za-z0-9]+/g, "-")}-${isoLocal().slice(0, 10)}.json`, backupJSON()); break;
    case "copyCons": { const ta = $("#consText"); ta.value = consensusMarkdown(); ta.select(); copyText(ta.value, "Copied the consensus. Paste it into the EMSim project in Claude."); break; }
    case "dlCons": saveFile(`emsim-review-consensus-${isoLocal().slice(0, 10)}.md`, consensusMarkdown()); break;
    case "doImport": doImport($("#importText").value); break;
    case "reset1": $("#resetRow").innerHTML = `<span class="warnline">This clears every answer, flag and comment you have made${SYNC.ref && !SYNC.readonly ? ", here and in the shared review" : ""}. You can undo it until you close the page.</span><button class="btn danger" data-act="reset2">Clear everything</button><button class="btn" data-act="reset0">Keep my answers</button>`; break;
    case "reset0": renderView(); break;
    case "reset2": mutate("cleared all answers", () => { S.answers = {}; S.flags = {}; }); toast("Cleared. Undo restores them.", true); break;
  }
  if (t.id === "undoBtn") undo();
  if (t.id === "redoBtn") redo();
  if (t.id === "whoBtn") openWho(false);
  if (t.id === "drawerBtn") $("#sidebar").classList.toggle("open");
  if (t.id === "clearF" || t.id === "clearF2") { UI.filters = { cases: [], pri: "all", status: "all", kind: "all", cat: "all", q: "" }; render(); }
});
document.addEventListener("submit", e => {
  if (e.target.id !== "whoForm") return;
  e.preventDefault();
  const name = $("#whoName").value.trim(); if (!name) return;
  mutate("set reviewer details", () => { S.reviewer.name = name; S.reviewer.role = $("#whoRole").value.trim(); S.reviewer.disclosures = $("#whoDisc").value.trim(); });
  closeModal();
});
document.addEventListener("change", e => {
  const id = e.target.id, f = UI.filters;
  if (id === "fStatus") f.status = e.target.value;
  else if (id === "fPri") f.pri = e.target.value;
  else if (id === "fKind") f.kind = e.target.value;
  else if (id === "fCat") f.cat = e.target.value;
  else if (id === "fSort") UI.sort = e.target.value;
  else if (id === "restoreFile" || id === "importFile") { readFile(e.target.files[0], id); return; }
  else return;
  render();
});
let searchTimer = null;
document.addEventListener("input", e => {
  const id = e.target.id; const q = currentQ();
  if (id === "search") { clearTimeout(searchTimer); const v = e.target.value; searchTimer = setTimeout(() => { UI.filters.q = v.trim(); renderSidebar(); if (UI.view === "review") renderView(); saveUI(); }, 180); return; }
  if (!q) return;
  if (id === "commentText") { textStart(`comment on ${q.id}`); textChanged(() => { ans(q.id).comment = e.target.value; }); }
  if (id === "otherText") { textStart(`own answer on ${q.id}`); textChanged(() => { const a = ans(q.id); a.other = e.target.value; a.committed = false; }); }
  if (id === "flagNote") { textStart(`flag note on ${q.id}`); textChanged(() => { if (S.flags[q.id]) S.flags[q.id].note = e.target.value; }); }
});
document.addEventListener("focusout", e => { if (["commentText", "otherText", "flagNote"].includes(e.target.id)) { textEnd(); persist(); renderProgress(); renderSidebar(); } });
document.addEventListener("keydown", e => {
  const tag = (e.target.tagName || "").toLowerCase();
  const typing = tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable;
  const mod = e.metaKey || e.ctrlKey;
  if (mod && (e.key === "z" || e.key === "Z") && !typing) { e.preventDefault(); if (e.shiftKey) redo(); else undo(); return; }
  if (mod && e.key === "y" && !typing) { e.preventDefault(); redo(); return; }
  if (e.key === "Escape") { if ($("#modal").innerHTML) { if (S.reviewer.name) closeModal(); } else if (typing) e.target.blur(); $("#sidebar").classList.remove("open"); return; }
  if (typing || mod || e.altKey) return;
  if ($("#modal").innerHTML) return;
  if (UI.view !== "review") { if (e.key === "/") { e.preventDefault(); const s = $("#search"); if (s) s.focus(); } return; }
  const k = e.key.toLowerCase();
  if (e.key === "Enter" && e.target.closest && e.target.closest(".opt")) { choose(e.target.closest(".opt").dataset.choice); return; }
  if (e.key === " " && e.target.closest && e.target.closest(".opt")) { e.preventDefault(); choose(e.target.closest(".opt").dataset.choice); return; }
  if (k === "a" || k === "b" || k === "c") { e.preventDefault(); choose(k.toUpperCase()); }
  else if (k === "o") { e.preventDefault(); choose("other"); }
  else if (k === "x") { e.preventDefault(); choose("abstain"); }
  else if (e.key === "Enter") { if (e.target.tagName !== "BUTTON" || e.target.dataset.act === "commit") { e.preventDefault(); commit(); } }
  else if (k === "f") { e.preventDefault(); toggleFlag(); }
  else if (k === "j" || e.key === "ArrowDown" && e.target === document.body) { e.preventDefault(); go(1); }
  else if (k === "k" || e.key === "ArrowUp" && e.target === document.body) { e.preventDefault(); go(-1); }
  else if (k === "n") { e.preventDefault(); nextOpen(); }
  else if (e.key === "/") { e.preventDefault(); const s = $("#search"); if (s) { $("#sidebar").classList.add("open"); s.focus(); } }
});
function readFile(file, which) {
  if (!file) return;
  const fr = new FileReader();
  fr.onload = () => { if (which === "importFile") doImport(fr.result); else doRestore(fr.result); };
  fr.readAsText(file);
}
function doRestore(text) {
  let st; try { st = parseRecord(text); } catch (e) { toast("That file is not an EMSim review backup or export"); return; }
  mutate("restored a backup", () => { S.reviewer = st.reviewer; S.answers = st.answers; S.flags = st.flags; });
  toast(`Restored ${Object.keys(st.answers).length} answers. Undo reverses this.`, true);
}
function doImport(text) {
  let st; try { st = parseRecord(text); } catch (e) { toast("Could not read that. Paste the full exported text, including the json block at the end."); return; }
  IMPORTS.push({ state: st, at: Date.now() }); lsSet(LS_IMPORTS, IMPORTS);
  toast(`Imported ${st.reviewer.name || "a reviewer"}: ${Object.keys(st.answers).length} answers`);
  render();
}

document.addEventListener("toggle", e => { if (e.target.id === "fullDetail") UI.fullOpen = e.target.open; }, true);
/* ============================== boot ============================== */
render();
if (!S.reviewer.name) openWho(true);
setTimeout(initCapabilities, 0);
window.__review = { S: () => S, UI, QS, exportMarkdown, consensusMarkdown, parseRecord, SYNC };
