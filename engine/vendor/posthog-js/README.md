posthog-js 1.434.17, `dist/array.no-external.js` from the npm package, unmodified except for
the removed sourceMappingURL line. Apache License 2.0 (LICENSE here).

The no-external build never loads further scripts from PostHog's servers, so session
recording, surveys and the toolbar cannot switch on from the PostHog dashboard, and the
site's Content-Security-Policy only needs PostHog's ingestion host in connect-src.
Inlined into site/index.html only, never into the local build.
