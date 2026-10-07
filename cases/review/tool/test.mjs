import { createRequire } from "module";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || "playwright");
import http from "http";
import fs from "fs";

const html = fs.readFileSync(new globalThis.URL("./out/test.html", import.meta.url));
const srv = http.createServer((req, res) => { res.writeHead(200, { "content-type": "text/html; charset=utf-8" }); res.end(html); }).listen(8765);
const URL = "http://127.0.0.1:8765/";
const results = []; let fails = 0;
const ok = (cond, msg) => { results.push((cond ? "PASS " : "FAIL ") + msg); if (!cond) fails++; };

// fake claude runtime: owner + db, shared across two "users" via a global store object passed in
const fakeClaude = (uid, owner, store) => `
(() => {
  const store = ${JSON.stringify(store)};
  window.__store = window.__store || {};
  const docs = window.__store; const subs = [];
  const snapDoc = p => ({ exists: !!docs[p], data: () => docs[p] ? JSON.parse(JSON.stringify(docs[p])) : undefined, metadata: { hasPendingWrites: false, fromCache: false }, id: p.split('/').pop() });
  const fire = () => subs.forEach(s => s());
  const db = {
    doc(p) { return { path: p, async get() { return snapDoc(p); }, async set(d) { if (JSON.stringify(d).length > 262144) throw { code: 'invalid_argument' }; docs[p] = JSON.parse(JSON.stringify(d)); window.__writes = (window.__writes || 0) + 1; fire(); }, onSnapshot(n) { const f = () => n(snapDoc(p)); subs.push(f); setTimeout(f, 0); return () => {}; } }; },
    collection(c) { return { onSnapshot(n) { const f = () => n({ docs: Object.keys(docs).filter(k => k.startsWith(c + '/')).map(snapDoc) }); subs.push(f); setTimeout(f, 0); return () => {}; } }; }
  };
  const user = { async isOwner() { return ${owner}; }, async id() { return '${uid}'; }, async can() { return true; }, async profiles(ids) { const o = {}; ids.forEach(i => o[i] = { id: i, name: 'Profile ' + i }); return o; } };
  window.claude = { use: async n => n === 'db' ? db : n === 'user' ? user : null };
})();`;

process.on("unhandledRejection",e=>{console.log(results.join("\n"));console.log("ERR",e.message.split("\n")[0]);process.exit(1)});
process.on("exit",()=>{console.log(results.join("\n"))});
const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" }).catch(() => chromium.launch());
const ctx = await browser.newContext({ viewport: { width: 1360, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", e => errors.push(String(e)));
page.on("console", m => { if (m.type() === "error" && !/ERR_TUNNEL|fonts/.test(m.text())) errors.push(m.text()); });
await page.goto(URL);
await page.waitForSelector("#whoForm");
ok(true, "welcome modal shows on first visit");
await page.fill("#whoName", "Dr Test Reviewer");
await page.fill("#whoRole", "EM attending");
await page.click('#whoForm button[type="submit"]');
ok(await page.locator("#whoForm").count() === 0, "modal closes after name");
ok((await page.textContent("#whoBtn")).includes("Dr Test Reviewer"), "reviewer chip shows name");
const nItems = await page.locator(".qi").count();
ok(nItems === 209, "sidebar lists all 209 questions (" + nItems + ")");
const firstId = await page.evaluate(() => window.__review.UI.current);
ok(await page.locator(".reveal").count() === 0, "recommendation hidden before commit");
ok(await page.locator(".rectag").count() === 0, "no recommendation tag before commit");
await page.keyboard.press("b");
ok(await page.getAttribute('.opt[data-choice="B"]', "aria-checked") === "true", "key B selects option B");
ok(await page.locator(".reveal").count() === 0, "still hidden after selecting, before commit");
await page.keyboard.press("Enter");
ok(await page.locator(".reveal").count() === 1, "recommendation revealed after commit");
ok(await page.locator(".rectag").count() === 1, "recommended option tagged after commit");
ok(/27 of 209 done/.test(await page.textContent("#prog")), "progress counts decided questions and the new answer");
let st = await page.evaluate(() => window.__review.S().answers);
const a1 = st[firstId];
ok(a1 && a1.committed && a1.firstChoice === "B" && a1.hash, "answer stored with first choice and hash");
const rec = await page.evaluate(id => window.__review.QS.find(q => q.id === id).recommended, firstId);
const other = ["A", "B", "C"].find(k => k !== "B");
await page.keyboard.press(other.toLowerCase());
ok((await page.textContent('[data-act="commit"]')).includes("Commit change"), "changing after reveal asks to commit the change");
await page.keyboard.press("Enter");
st = await page.evaluate(() => window.__review.S().answers);
ok(st[firstId].choice === other && st[firstId].changedAfterReveal === true && st[firstId].firstChoice === "B", "change after reveal recorded");
// confidence + comment
await page.click('[data-conf="high"]');
await page.click('[data-act="comment"]');
await page.fill("#commentText", "Checked against the seed.");
await page.locator("#commentText").blur();
st = await page.evaluate(() => window.__review.S().answers);
ok(st[firstId].confidence === "high" && st[firstId].comment === "Checked against the seed.", "confidence and comment saved");
// next + flag
await page.keyboard.press("j");
const secondId = await page.evaluate(() => window.__review.UI.current);
ok(secondId !== firstId, "J moves to next question");
await page.keyboard.press("f");
ok((await page.textContent('[data-act="flag"]')).includes("Flagged"), "F flags question");
await page.fill("#flagNote", "Ask toxicology");
await page.locator("#flagNote").blur();
st = await page.evaluate(() => window.__review.S());
ok(st.flags[secondId] && st.flags[secondId].note === "Ask toxicology", "flag note saved");
ok((await page.textContent("#prog")).includes("1 flagged"), "progress counts flagged");
// undo / redo
await page.click("#undoBtn"); // undo flag note
await page.click("#undoBtn"); // undo flag
st = await page.evaluate(() => window.__review.S());
ok(!st.flags[secondId], "undo removes flag");
await page.click("#redoBtn");
st = await page.evaluate(() => window.__review.S());
ok(!!st.flags[secondId], "redo restores flag");
await page.keyboard.press("Control+z");
st = await page.evaluate(() => window.__review.S());
ok(!st.flags[secondId], "Ctrl Z undoes");
await page.keyboard.press("Control+Shift+z");
st = await page.evaluate(() => window.__review.S());
ok(!!st.flags[secondId], "Ctrl Shift Z redoes");
// own answer: commit disabled until text
await page.keyboard.press("n");
const thirdId = await page.evaluate(() => window.__review.UI.current);
ok(thirdId !== secondId && thirdId !== firstId, "N goes to next unanswered");
await page.keyboard.press("o");
ok(await page.isDisabled('[data-act="commit"]'), "own answer cannot commit while empty");
await page.fill("#otherText", "Make it harmful only after the echo.");
ok(!(await page.isDisabled('[data-act="commit"]')), "own answer commit enabled after typing");
await page.click('[data-act="commit"]');
st = await page.evaluate(() => window.__review.S().answers);
ok(st[thirdId].committed && st[thirdId].choice === "other", "own answer committed");
// abstain
await page.keyboard.press("n");
const fourthId = await page.evaluate(() => window.__review.UI.current);
await page.keyboard.press("x"); await page.keyboard.press("Enter");
st = await page.evaluate(() => window.__review.S().answers);
ok(st[fourthId].choice === "abstain" && st[fourthId].committed, "abstain committed");
// filters
await page.click('.chip[data-case="DIPH"]');
ok(await page.locator(".qi").count() === 46, "DIPH filter shows 46");
ok((await page.evaluate(() => window.__review.UI.current)).startsWith("DIPH"), "current question follows filter");
await page.selectOption("#fSort", "category");
ok(await page.locator(".grp").count() > 3, "sort by category groups");
await page.selectOption("#fStatus", "flagged");
ok(await page.locator(".qi").count() === (secondId.startsWith("DIPH") ? 1 : 0), "status filter flagged");
await page.click("#clearF");
ok(await page.locator(".qi").count() === 209, "clear filters restores all");
await page.fill("#search", "physostigmine");
await page.waitForTimeout(300);
const ns = await page.locator(".qi").count();
ok(ns > 0 && ns < 30, "search narrows (" + ns + ")");
await page.fill("#search", "");
await page.waitForTimeout(300);
// persistence across reload
await page.reload();
await page.waitForSelector(".qi");
st = await page.evaluate(() => window.__review.S());
ok(Object.values(st.answers).filter(a => a.committed).length >= 3 && st.flags[secondId], "answers and flags persist after reload");
ok(await page.locator("#whoForm").count() === 0, "no welcome modal once named");
// summary/export
await page.click('[data-view="summary"]');
const exp = await page.inputValue("#exportText");
ok(exp.includes("## Instructions for Claude") && exp.includes("### " + firstId), "export has instructions and answers");
ok(exp.includes("Changed after seeing the recommendation"), "export records changed after reveal");
ok(exp.includes("Flagged for later, do not apply") && exp.includes(secondId + "."), "export lists flags with notes");
ok((exp.match(/```/g) || []).length % 2 === 0, "export code fences balanced");
ok(!/[—;]/.test(exp.split("## Machine-readable record")[0].replace(/Implementation: .*$/gm, "")), "export prose has no em dash or semicolon");
const rec2 = await page.evaluate(t => { const s = window.__review.parseRecord(t); return Object.keys(s.answers).length; }, exp);
ok(rec2 === 3, "export round-trips through parser (" + rec2 + ")");
// import into consensus (local mode, not owner)
await page.click('[data-view="guide"]');
ok((await page.textContent("#view")).includes("How this review works"), "guide renders");
await page.evaluate(t => { localStorage.setItem("emsim-review-imports-v1", JSON.stringify([{ state: window.__review.parseRecord(t.replaceAll("Dr Test Reviewer", "Dr Imported")), at: 1 }])); }, exp);
await page.reload(); await page.waitForSelector(".qi");
ok(await page.locator('[data-view="consensus"]').count() === 1, "consensus tab appears with imports");
await page.click('[data-view="consensus"]');
const ctext = await page.textContent("#view");
ok(ctext.includes("Dr Imported") && ctext.includes("Unanimous"), "consensus shows imported reviewer and unanimity");
const cons = await page.inputValue("#consText");
ok(cons.includes("## Agreed") && cons.includes("Dr Imported"), "consensus export builds");
// reset with inline confirm then undo
await page.click('[data-view="summary"]');
await page.click('[data-act="reset1"]');
await page.click('[data-act="reset2"]');
st = await page.evaluate(() => window.__review.S());
ok(Object.keys(st.answers).length === 0, "reset clears");
await page.click("#undoBtn");
st = await page.evaluate(() => window.__review.S());
ok(Object.keys(st.answers).length >= 3, "undo reverses reset");
await page.screenshot({ path: "./out/shot-summary.png", fullPage: false });
await page.click('[data-view="review"]');
await page.click(`.qi[data-q="${firstId}"]`);
await page.screenshot({ path: "./out/shot-desktop.png" });
ok(errors.length === 0, "no page errors (" + errors.join(" | ") + ")");
await ctx.close();

// ---------- shared store (fake runtime) ----------
const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 860 } });
await ctx2.addInitScript(fakeClaude("u_owner", true, {}));
const p2 = await ctx2.newPage(); const err2 = [];
p2.on("pageerror", e => err2.push(String(e)));
await p2.goto(URL); await p2.waitForSelector("#whoForm");
await p2.fill("#whoName", "Owner Doc"); await p2.click('#whoForm button[type="submit"]');
await p2.waitForTimeout(300);
ok(await p2.locator('[data-view="consensus"]').count() === 1, "owner sees consensus tab");
await p2.keyboard.press("a"); await p2.keyboard.press("Enter");
await p2.waitForTimeout(1800);
const store = await p2.evaluate(() => window.__store);
ok(store["reviews/u_owner"] && Object.keys(store["reviews/u_owner"].answers).length === 1, "answer written to reviews/<uid>");
ok((await p2.getAttribute("#sync","class")).includes("shared"), "sync badge shows shared");
// simulate a second reviewer writing
await p2.evaluate(() => { window.__store["reviews/u_other"] = { reviewer: { name: "Dr Second", role: "Tox" }, answers: {}, flags: {}, updatedAt: Date.now() }; });
await p2.evaluate(() => { const qid = window.__review.QS[0].id; const d = window.__store["reviews/u_other"]; d.answers[qid] = { choice: "C", committed: true, revealed: true, firstChoice: "C", hash: window.__review.QS[0].hash, comment: "Disagree" }; });
await p2.click('[data-view="consensus"]');
await p2.evaluate(() => window.__store && null);
// trigger snapshot by another write
await p2.click('[data-view="review"]'); await p2.keyboard.press("f"); await p2.waitForTimeout(1600);
await p2.click('[data-view="consensus"]');
const ct2 = await p2.textContent("#view");
ok(ct2.includes("Dr Second") && ct2.includes("Owner Doc"), "owner consensus lists both reviewers");
await p2.click('[data-csf="split"]');
ok((await p2.textContent("#view")).includes("Split"), "split filter shows the disagreement");
ok(err2.length === 0, "no page errors with shared store (" + err2.join(" | ") + ")");
await ctx2.close();

// ---------- non-owner reviewer: no consensus ----------
const ctx3 = await browser.newContext({ viewport: { width: 1280, height: 860 } });
await ctx3.addInitScript(fakeClaude("u_rev", false, {}));
const p3 = await ctx3.newPage();
await p3.goto(URL); await p3.waitForSelector("#whoForm");
await p3.fill("#whoName", "Reviewer Two"); await p3.click('#whoForm button[type="submit"]');
await p3.waitForTimeout(300);
ok(await p3.locator('[data-view="consensus"]').count() === 0, "non-owner does not see consensus tab");
await ctx3.close();

// ---------- phone width, dark ----------
const ctx4 = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: "dark" });
const p4 = await ctx4.newPage(); const err4 = [];
p4.on("pageerror", e => err4.push(String(e)));
await p4.goto(URL); await p4.waitForSelector("#whoForm");
await p4.fill("#whoName", "Phone Doc"); await p4.click('#whoForm button[type="submit"]');
const sw = await p4.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
ok(sw[0] <= sw[1], "no horizontal scroll at 390px (" + sw + ")");
await p4.screenshot({ path: "./out/shot-phone-dark.png" });
await p4.click("#drawerBtn"); await p4.waitForTimeout(300);
await p4.screenshot({ path: "./out/shot-phone-drawer.png" });
const bg = await p4.evaluate(() => getComputedStyle(document.body).backgroundColor);
ok(bg === "rgb(243, 246, 251)", "stays in day mode when the OS is dark (" + bg + ")");
ok(err4.length === 0, "no page errors on phone");
await ctx4.close();
await browser.close(); srv.close();
console.log(results.join("\n")); console.log(fails ? fails + " FAILED" : "ALL PASSED");
