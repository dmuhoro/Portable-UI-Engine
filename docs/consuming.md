# Consuming Portable UI Engine

## Installation
- npm: `npm install @universal-ui/engine`
- Git: `npm install github:dmuhoro/Portable-UI-Engine#chore/ci-bootstrap`

## Usage (Vanilla HTML)
```html
<script type="module">
  import '@universal-ui/engine';
</script>
<ui-button variant="primary">Hello</ui-button>
```

## Theming
Use CSS custom properties from `packages/tokens/css/variables.css`. Themes: light, dark, high-contrast.

## SSR Notes
For Next.js, import and register components in a client component only.
