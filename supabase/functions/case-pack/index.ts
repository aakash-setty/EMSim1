// EMSim v0.18: the case-pack edge function.
//
// POST { "prefix": "CHFE" } with the signed-in user's access token. Returns the pack JSON
// exactly as uploaded, so the browser can check it against the SHA-256 in the site build.
//
// Deploy: Supabase dashboard, Edge Functions, Deploy a new function, name it `case-pack`,
// paste this file. Keep "Verify JWT" on. Set the secrets listed in docs/deployment.md.
//
// Order of checks: method, origin, signed-in user, case name, then the database decides
// (active account, rate limit) and logs the attempt, then storage. Nothing is read from
// storage for a request that fails an earlier check.

import { createClient } from "npm:@supabase/supabase-js@2.117.2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";

// The secret key. Projects on the legacy keys have SUPABASE_SERVICE_ROLE_KEY; projects on
// the new keys have SUPABASE_SECRET_KEYS, a JSON object of named secret keys.
function secretKey(): string {
  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return legacy;
  try {
    const keys = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}");
    const first = Object.values(keys)[0];
    return typeof first === "string" ? first : "";
  } catch {
    return "";
  }
}

// Comma-separated list of the site origins allowed to call this function, for example
// "https://emsim.vercel.app,http://localhost:8000". Required: with none set, every browser
// request is refused.
const ALLOWED_ORIGINS = (Deno.env.get("ALLOWED_ORIGINS") ?? "")
  .split(",").map((s) => s.trim().replace(/\/+$/, "")).filter(Boolean);
const PER_HOUR = positiveInt(Deno.env.get("CASE_LOADS_PER_HOUR"), 20);
const PER_DAY = positiveInt(Deno.env.get("CASE_LOADS_PER_DAY"), 100);
const BUCKET = "case-packs";
const PREFIX_RE = /^[A-Z][A-Z0-9]{1,15}$/;

function positiveInt(v: string | undefined, fallback: number): number {
  const n = Number(v);
  return Number.isInteger(n) && n > 0 ? n : fallback;
}

function corsHeaders(origin: string | null): Record<string, string> {
  const h: Record<string, string> = {
    "Vary": "Origin",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
    "Access-Control-Max-Age": "600",
  };
  if (origin && ALLOWED_ORIGINS.includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}

function reply(status: number, body: unknown, origin: string | null): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(origin), "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("Origin");

  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(origin) });
  }
  if (req.method !== "POST") return reply(405, { error: "method_not_allowed" }, origin);
  // Browsers always send Origin on a cross-origin POST. A request from anywhere else is
  // refused here too; this is not the security boundary (the token is), but it keeps
  // other sites' pages from spending a user's quota.
  if (!origin || !ALLOWED_ORIGINS.includes(origin)) return reply(403, { error: "origin_not_allowed" }, origin);

  const key = secretKey();
  if (!SUPABASE_URL || !key) return reply(500, { error: "not_configured" }, origin);

  const auth = req.headers.get("Authorization") ?? "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7).trim() : "";
  if (!token) return reply(401, { error: "signin_required" }, origin);

  const admin = createClient(SUPABASE_URL, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  // Asks the Auth server, so a deleted or banned user is refused even with an unexpired token.
  const { data: userData, error: userError } = await admin.auth.getUser(token);
  const user = userData?.user;
  if (userError || !user) return reply(401, { error: "signin_required" }, origin);
  // Invited accounts are created confirmed. An anonymous session, or an address nobody has
  // confirmed, gets nothing even if a setting is later changed to allow them to exist.
  if (user.is_anonymous || !user.email_confirmed_at) return reply(403, { error: "no_access" }, origin);

  let prefix = "";
  try {
    const body = await req.json();
    prefix = typeof body?.prefix === "string" ? body.prefix : "";
  } catch {
    return reply(400, { error: "bad_request" }, origin);
  }
  if (!PREFIX_RE.test(prefix)) return reply(400, { error: "bad_request" }, origin);

  const { data: verdict, error: rpcError } = await admin.rpc("claim_case_load", {
    p_user: user.id, p_prefix: prefix, p_per_hour: PER_HOUR, p_per_day: PER_DAY,
  });
  if (rpcError) {
    console.error("claim_case_load failed", rpcError.message);
    return reply(500, { error: "server_error" }, origin);
  }
  if (verdict === "rate_limited") return reply(429, { error: "rate_limited" }, origin);
  if (verdict !== "ok") return reply(403, { error: "no_access" }, origin);

  const { data: file, error: fileError } = await admin.storage.from(BUCKET).download(`${prefix}.json`);
  if (fileError || !file) return reply(404, { error: "not_found" }, origin);

  // Sent as the exact bytes stored, never re-serialised: the browser hashes them.
  return new Response(await file.arrayBuffer(), {
    status: 200,
    headers: { ...corsHeaders(origin), "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
});
