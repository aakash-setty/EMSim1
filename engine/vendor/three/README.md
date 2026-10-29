# three.js, vendored

`three.min.js` is three.js 0.186.1 (published 24 September 2026, MIT license, see `LICENSE`)
with `OrbitControls` from its examples, bundled into one classic script that sets the global
`THREE`. The procedures (`engine/procsim-*.js`) use it. It is loaded only when a procedure
is opened, never with the case list.

Rebuild (28 October 2026):

```
npm i three@0.186.1 esbuild@0.25.10
npx esbuild build-entry.js --bundle --minify --format=iife --target=es2019 \
  --outfile=three.min.js --legal-comments=none
```

`build-entry.js` is the entry file used. The build puts the license text at the top of the
procedure script it writes.
