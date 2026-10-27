# Component Gallery

The gallery at `index.html` presents all nine `ui-*` primitives, supports category and text filtering, switches among the generated themes, and inspects computed CSS tokens. It is a static browser app served by the root Vite dev server at `/apps/docs/`.

The component previews load the root engine ESM entry and generated `theme.css`. Interactive behaviors are covered by `npm run test:showcases`.
