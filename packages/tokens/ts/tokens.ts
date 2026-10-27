export const cssVariables = {
  'color-brand-primary': '#4f46e5',
  'color-brand-primaryHover': '#4338ca',
  'color-surface-background': '#0b1026',
  'color-surface-panel': '#10162a',
  'color-text-primary': '#e6e8ee',
  'color-text-secondary': '#b9bfd3',
  'color-border': '#263056',
  'color-success': '#22c55e',
  'color-warning': '#f59e0b',
  'color-danger': '#ef4444',
  'spacing-xs': '4px',
  'spacing-sm': '8px',
  'spacing-md': '16px',
  'spacing-lg': '24px',
  'spacing-xl': '32px',
  'radius-sm': '6px',
  'radius-md': '10px',
  'radius-lg': '14px',
  'typography-fontSans': ''Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
  'typography-sizeBase': '16px',
  'typography-sizeSm': '14px',
  'typography-sizeLg': '18px',
} as const;

export const tokens = cssVariables;
export type TokenKey = keyof typeof cssVariables;
