/**
 * engine.js
 * Portable UI Engine - Unified Master Barrel Distribution File
 * Imports, safely defines, and exports all Native Web Components.
 * Attaches the global UniversalUI namespace controller to the window object.
 */

import './universal-app-shell.js';
import './universal-form.js';
import './universal-metric-grid.js';
import './universal-data-table.js';
import './universal-saas-dashboard.js';
import './universal-billing-funnel.js';

// Pre-defined Theme Presets Dictionary
const THEME_PRESETS = {
  light: {
    '--color-bg-app': '#f8fafc',
    '--color-bg-surface': '#ffffff',
    '--color-bg-surface-elevated': '#ffffff',
    '--color-bg-hover': '#f1f5f9',
    '--color-bg-active': '#e2e8f0',
    '--color-bg-stripe': '#f8fafc',
    '--color-text-primary': '#0f172a',
    '--color-text-secondary': '#475569',
    '--color-text-muted': '#94a3b8',
    '--color-text-inverse': '#ffffff',
    '--color-border': '#e2e8f0',
    '--color-border-strong': '#cbd5e1',
    '--color-primary': '#2563eb',
    '--color-primary-hover': '#1d4ed8',
    '--color-primary-light': '#eff6ff',
    '--color-accent': '#0d9488',
    '--radius-sm': '0.25rem',
    '--radius-md': '0.375rem',
    '--radius-lg': '0.5rem',
    '--radius-xl': '0.75rem',
  },
  dark: {
    '--color-bg-app': '#0f172a',
    '--color-bg-surface': '#1e293b',
    '--color-bg-surface-elevated': '#334155',
    '--color-bg-hover': '#334155',
    '--color-bg-active': '#475569',
    '--color-bg-stripe': '#182234',
    '--color-text-primary': '#f8fafc',
    '--color-text-secondary': '#cbd5e1',
    '--color-text-muted': '#64748b',
    '--color-text-inverse': '#0f172a',
    '--color-border': '#334155',
    '--color-border-strong': '#475569',
    '--color-primary': '#3b82f6',
    '--color-primary-hover': '#60a5fa',
    '--color-primary-light': '#1e3a8a',
    '--color-accent': '#14b8a6',
    '--radius-sm': '0.25rem',
    '--radius-md': '0.375rem',
    '--radius-lg': '0.5rem',
    '--radius-xl': '0.75rem',
  },
  corporate: {
    '--color-bg-app': '#f3f4f6',
    '--color-bg-surface': '#ffffff',
    '--color-bg-surface-elevated': '#f9fafb',
    '--color-bg-hover': '#f3f4f6',
    '--color-bg-active': '#e5e7eb',
    '--color-bg-stripe': '#f9fafb',
    '--color-text-primary': '#111827',
    '--color-text-secondary': '#4b5563',
    '--color-text-muted': '#9ca3af',
    '--color-text-inverse': '#ffffff',
    '--color-border': '#e5e7eb',
    '--color-border-strong': '#d1d5db',
    '--color-primary': '#1e40af',
    '--color-primary-hover': '#1e3a8a',
    '--color-primary-light': '#dbeafe',
    '--color-accent': '#0369a1',
    '--radius-sm': '2px',
    '--radius-md': '4px',
    '--radius-lg': '6px',
    '--radius-xl': '8px',
  },
  cyberpunk: {
    '--color-bg-app': '#0d0221',
    '--color-bg-surface': '#150534',
    '--color-bg-surface-elevated': '#220b4f',
    '--color-bg-hover': '#2a0e5f',
    '--color-bg-active': '#39137d',
    '--color-bg-stripe': '#12042c',
    '--color-text-primary': '#00f5d4',
    '--color-text-secondary': '#f72585',
    '--color-text-muted': '#7209b7',
    '--color-text-inverse': '#0d0221',
    '--color-border': '#39137d',
    '--color-border-strong': '#7209b7',
    '--color-primary': '#f72585',
    '--color-primary-hover': '#b5179e',
    '--color-primary-light': '#3a0ca3',
    '--color-accent': '#4cc9f0',
    '--radius-sm': '0px',
    '--radius-md': '0px',
    '--radius-lg': '0px',
    '--radius-xl': '0px',
  },
  midnight: {
    '--color-bg-app': '#030712',
    '--color-bg-surface': '#111827',
    '--color-bg-surface-elevated': '#1f2937',
    '--color-bg-hover': '#1f2937',
    '--color-bg-active': '#374151',
    '--color-bg-stripe': '#0b0f19',
    '--color-text-primary': '#f9fafb',
    '--color-text-secondary': '#9ca3af',
    '--color-text-muted': '#6b7280',
    '--color-text-inverse': '#111827',
    '--color-border': '#1f2937',
    '--color-border-strong': '#374151',
    '--color-primary': '#6366f1',
    '--color-primary-hover': '#4f46e5',
    '--color-primary-light': '#312e81',
    '--color-accent': '#8b5cf6',
    '--radius-sm': '0.375rem',
    '--radius-md': '0.5rem',
    '--radius-lg': '0.75rem',
    '--radius-xl': '1rem',
  },
  emerald: {
    '--color-bg-app': '#f0fdf4',
    '--color-bg-surface': '#ffffff',
    '--color-bg-surface-elevated': '#ffffff',
    '--color-bg-hover': '#dcfce7',
    '--color-bg-active': '#bbf7d0',
    '--color-bg-stripe': '#f6fef9',
    '--color-text-primary': '#064e3b',
    '--color-text-secondary': '#047857',
    '--color-text-muted': '#34d399',
    '--color-text-inverse': '#ffffff',
    '--color-border': '#a7f3d0',
    '--color-border-strong': '#6ee7b7',
    '--color-primary': '#059669',
    '--color-primary-hover': '#047857',
    '--color-primary-light': '#ecfdf5',
    '--color-accent': '#10b981',
    '--radius-sm': '0.25rem',
    '--radius-md': '0.5rem',
    '--radius-lg': '0.75rem',
    '--radius-xl': '1rem',
  }
};

/**
 * Global UniversalUI Engine Controller Namespace
 */
const UniversalUI = {
  version: '2.0.0-dist',
  currentTheme: 'light',
  presets: THEME_PRESETS,

  /**
   * Dynamically mutates design system tokens at runtime.
   * @param {string} themeName - Preset key name ('light' | 'dark' | 'corporate' | 'cyberpunk' | 'midnight' | 'emerald')
   * @param {Object} customTokensObject - Key-value overrides (e.g. { '--color-primary': '#ff0055' })
   */
  setTheme(themeName, customTokensObject = {}) {
    const root = document.documentElement;
    this.currentTheme = themeName || 'light';
    root.setAttribute('data-theme', this.currentTheme);

    // 1. Clear any inline style overrides first to allow clean preset switching
    const preset = THEME_PRESETS[this.currentTheme];
    if (preset) {
      Object.entries(preset).forEach(([token, val]) => {
        root.style.setProperty(token, val);
      });
    }

    // 2. Apply explicit custom token overrides
    if (customTokensObject && typeof customTokensObject === 'object') {
      Object.entries(customTokensObject).forEach(([token, val]) => {
        const key = token.startsWith('--') ? token : `--${token}`;
        root.style.setProperty(key, val);
      });
    }

    // 3. Dispatch global theme shift event across shadow roots
    window.dispatchEvent(
      new CustomEvent('universal-theme-change', {
        detail: {
          theme: this.currentTheme,
          tokens: customTokensObject
        },
        bubbles: true,
        composed: true,
      })
    );

    return this.currentTheme;
  },

  /**
   * Returns list of currently registered engine component tags.
   */
  getRegisteredComponents() {
    const components = [
      'universal-app-shell',
      'universal-form',
      'universal-metric-grid',
      'universal-data-table',
      'universal-saas-dashboard',
      'universal-billing-funnel'
    ];
    return components.filter(tag => Boolean(customElements.get(tag)));
  }
};

// Bind to window object for global script / CDN usage
if (typeof window !== 'undefined') {
  window.UniversalUI = UniversalUI;
}

export { UniversalUI };
