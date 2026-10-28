#!/usr/bin/env bash
# End-to-end check of the deployed build against a mock Supabase and the real edge function.
# Needs node with playwright, and deno. Run from the repository root after a full build:
#   bash engine/site-check/run.sh
# Ports: 54321 mock Supabase, 8000 edge function (deno), 8080 site with the mock configured,
# 8090 site with no Supabase settings, 8091 site as built (no network calls are made to it;
# the check only loads the page). Test account: res@example.com / right-password (mock only).
set -euo pipefail
ROOT=$(pwd); T=$(mktemp -d)
mkdir -p "$T/site" "$T/site0" "$T/site1"
cp site/index.html "$T/site1/index.html"
python3 - "$T" <<'PY'
import json, re, sys
t = sys.argv[1]
s = open("site/index.html", encoding="utf-8").read()
m = re.search(r'<script type="application/json" id="access-data">(.*?)</script>', s, re.S)
built = json.loads(m.group(1))
def write(path, **over):
    a = dict(built, **over)
    open(path, "w", encoding="utf-8").write(s[:m.start(1)] + json.dumps(a) + s[m.end(1):])
write(t + "/site/index.html", supabaseUrl="http://localhost:54321", supabaseKey="anon-key", googleSignIn=True)
write(t + "/site0/index.html", supabaseUrl="", supabaseKey="")
# The built site and its headers must agree: a configured project has to be in connect-src,
# or every sign-in is blocked by the browser.
csp = next(h["value"] for h in json.load(open("vercel.json"))["headers"][0]["headers"]
           if h["key"] == "Content-Security-Policy")
connect = next(d for d in csp.split("; ") if d.startswith("connect-src ")).split()[1:]
url = (built.get("supabaseUrl") or "").rstrip("/")
ok = (url in connect) if url else True
print(("ok   " if ok else "FAIL ") + "built site's Supabase URL is allowed by the CSP" +
      ("" if url else " (no URL configured)"))
open(t + "/configured", "w").write("1" if url and built.get("supabaseKey") else "0")
if not ok:
    sys.exit(1)
PY
# --node-modules-dir=none: the repository has a package.json, and with one present Deno 2
# looks for npm packages in node_modules, where supabase-js is not installed.
PACKS_DIR="$ROOT/private-packs" node engine/site-check/mock.js > "$T/mock.log" 2>&1 & P1=$!
SUPABASE_URL=http://localhost:54321 SUPABASE_SERVICE_ROLE_KEY=svc ALLOWED_ORIGINS=http://localhost:8080 \
  deno run --node-modules-dir=none --no-lock --allow-net --allow-env supabase/functions/case-pack/index.ts > "$T/deno.log" 2>&1 & P2=$!
node engine/site-check/serve.js "$T/site" 8080 "$ROOT/vercel.json" http://localhost:54321 > /dev/null 2>&1 & P3=$!
node engine/site-check/serve.js "$T/site0" 8090 "$ROOT/vercel.json" "" > /dev/null 2>&1 & P4=$!
node engine/site-check/serve.js "$T/site1" 8091 "$ROOT/vercel.json" "" > /dev/null 2>&1 & P5=$!
trap 'kill $P1 $P2 $P3 $P4 $P5 2>/dev/null || true' EXIT
for i in $(seq 1 60); do curl -s -o /dev/null http://localhost:8000/ && break; sleep 1; done
node engine/site-check/flow.js
SITE_CONFIGURED=$(cat "$T/configured") node engine/site-check/deep.js
node engine/site-check/google.js
# Saved progress (28 October 2026): autosave, resume, finish, delete, the version notice.
node engine/site-check/progress.js
# The pack publisher (run by the GitHub Action) against the mock bucket: uploads all, then
# finds them all present, then refuses a pack that reads back altered.
curl -s -XPOST http://localhost:54321/__ctl -d '{"storeOnly":true,"tamper":false}' > /dev/null
P="env SUPABASE_URL=http://localhost:54321 SUPABASE_SECRET_KEY=sb_secret_test node engine/publish_packs.js"
$P | tail -1 | grep -q ", 0 already present" && echo "ok   publisher uploads every pack" || echo "FAIL publisher uploads every pack"
$P | tail -1 | grep -q " 0 uploaded" && echo "ok   publisher skips packs already there" || echo "FAIL publisher skips packs already there"
curl -s -XPOST http://localhost:54321/__ctl -d '{"storeOnly":true,"tamper":true}' > /dev/null
curl -s -XPOST http://localhost:54321/__ctl -d '{}' > /dev/null
if $P > /dev/null 2>&1; then echo "FAIL publisher trusts a pack that reads back altered"; else echo "ok   publisher refuses a pack that reads back altered"; fi
