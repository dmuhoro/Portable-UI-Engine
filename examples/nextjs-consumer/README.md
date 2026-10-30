
## Offline/workaround (if npm registry unreachable)
If `npm ci`/`npm install` fails with `ENETUNREACH` or cannot fetch `next`:
1. Use a cached `next` binary from another environment, or copy `node_modules/.bin/next` and deps.
2. Or install from local tarball/cache: `npm install --offline` if cached.
3. Alternatively build with `npx --yes next@15.5.28 build` only if cached; otherwise document as blocked by network.
This repo's CI may have network access; locally offline is a known constraint.
