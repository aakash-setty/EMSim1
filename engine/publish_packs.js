#!/usr/bin/env node
/* Upload the case packs of this build to the private Supabase bucket.

   Run by .github/workflows/publish-packs.yml after every push to main, straight after a
   full build. Not meant to be run by hand: it needs the project's SECRET key, which lives
   only in the GitHub secret SUPABASE_SECRET_KEY.

   Packs are stored by content, at case-packs/<PREFIX>/<sha256>.json, using the hash that
   site/index.html already carries for each locked case. So an upload never replaces what an
   older site build is reading, and the site and the packs can go live in either order.
   A pack already in the bucket with the right bytes is left alone. Every upload is read back
   and hashed before the script reports success.

   Environment:
     SUPABASE_SECRET_KEY   required. sb_secret_... (or the legacy service_role key)
     SUPABASE_URL          optional. Defaults to supabaseUrl in engine/site-config.json

   Exit code 0 only when every locked case in site/index.html has its exact pack in the
   bucket. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const ROOT = path.join(__dirname, '..');

function die(msg) { console.error('publish_packs: ' + msg); process.exit(1); }
const sha256 = buf => crypto.createHash('sha256').update(buf).digest('hex');

const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'engine/site-config.json'), 'utf8'));
const url = (process.env.SUPABASE_URL || cfg.supabaseUrl || '').replace(/\/+$/, '');
const key = (process.env.SUPABASE_SECRET_KEY || '').trim();
if (!url) die('no Supabase URL in engine/site-config.json');
if (!key) die('SUPABASE_SECRET_KEY is not set. Add it under the repository Settings, Secrets and variables, Actions.');
if (key.startsWith('sb_publishable_')) die('SUPABASE_SECRET_KEY holds the publishable key. It needs the secret key (sb_secret_...).');

// The locked cases, and the hash of each, exactly as the site that is being deployed has them.
const site = fs.readFileSync(path.join(ROOT, 'site/index.html'), 'utf8');
const m = site.match(/<script type="application\/json" id="cases-data">([\s\S]*?)<\/script>/);
if (!m) die('site/index.html has no cases-data block');
// Procedures (28 October 2026) are locked packs too, in their own block.
const mp = site.match(/<script type="application\/json" id="procedures-data">([\s\S]*?)<\/script>/);
const stubs = JSON.parse(m[1]).filter(c => c.locked).concat(mp ? JSON.parse(mp[1]).filter(c => c.locked) : []);
if (!stubs.length) die('site/index.html has no locked cases');

// The same supabase-js the site uses (engine/vendor), so no npm install is needed.
const lib = fs.readFileSync(path.join(ROOT, 'engine/vendor/supabase-js/supabase.umd.js'), 'utf8');
vm.runInThisContext(lib);
// eslint-disable-next-line no-undef
const client = supabase.createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
const bucket = client.storage.from('case-packs');

async function remoteHash(p) {
  const { data, error } = await bucket.download(p);
  if (error || !data) return null;
  return sha256(Buffer.from(await data.arrayBuffer()));
}

(async () => {
  let uploaded = 0, present = 0;
  for (const s of stubs) {
    const file = path.join(ROOT, 'private-packs', s.prefix + '.json');
    if (!fs.existsSync(file)) die(`private-packs/${s.prefix}.json is missing. Run a full build first.`);
    const bytes = fs.readFileSync(file);
    if (sha256(bytes) !== s.packSha256)
      die(`private-packs/${s.prefix}.json does not match the hash in site/index.html. Run a full build, commit site/ and push again.`);
    const p = `${s.prefix}/${s.packSha256}.json`;
    if (await remoteHash(p) === s.packSha256) { present++; console.log(`  ${p}  already in the bucket`); continue; }
    const { error } = await bucket.upload(p, bytes, { contentType: 'application/json', upsert: true });
    if (error) die(`upload of ${p} failed: ${error.message || error}`);
    if (await remoteHash(p) !== s.packSha256) die(`${p} was uploaded but reads back with different bytes`);
    uploaded++; console.log(`  ${p}  uploaded and verified (${bytes.length} bytes)`);
  }
  console.log(`publish_packs: ${stubs.length} cases, ${uploaded} uploaded, ${present} already present`);
})().catch(e => die(e && e.message || String(e)));
