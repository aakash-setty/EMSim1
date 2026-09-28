# supabase-js, vendored

`supabase.umd.js` is `dist/umd/supabase.js` from the npm package `@supabase/supabase-js`
version 2.117.2, unmodified. MIT licence, `LICENSE` beside it. Inlined into `site/index.html`
only, never into the local build, by `engine/build_simulator.py`.

SHA-256 59d39487c3589843b410322d8a3d562ce022aba1e5ccb16898ef3fb2a0da2ecd, checked against two
independent downloads of the package when it was added.

It is vendored rather than loaded from a CDN so the deployed page depends on no third party
for sign-in, and so the Content-Security-Policy can pin it by hash. To update: replace the
file from a newer package, update the version here and in `build_simulator.py`, and keep the
edge function's import (`supabase/functions/case-pack/index.ts`) on the same version.
