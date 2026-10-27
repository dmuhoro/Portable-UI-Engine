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
import './universal-ai-bridge.js';
import './elements/ui-primitives.js';

// Pre-defined Theme Presets Dictionary
const THEME_PRESETS = {
  'warm-precision': {},
  'technical-oceanic': {},
  'swiss-minimalist': {},
  light: {},
  dark: {},
  corporate: {},
  cyberpunk: {},
  midnight: {},
  emerald: {},
};

/**
 * Global UniversalUI Engine Controller Namespace
 */
const UniversalUI = {
  version: '2.0.0-dist',
  currentTheme: 'warm-precision',
  presets: THEME_PRESETS,

  /**
   * Dynamically mutates design system tokens at runtime.
   * @param {string} themeName - Preset key name ('light' | 'dark' | 'corporate' | 'cyberpunk' | 'midnight' | 'emerald')
   * @param {Object} customTokensObject - Key-value overrides (e.g. { '--color-primary': '#ff0055' })
   */
  setTheme(themeName, customTokensObject = {}) {
    const root = document.documentElement;
    this.currentTheme = THEME_PRESETS[themeName] ? themeName : 'warm-precision';
    root.setAttribute('data-theme', this.currentTheme);

    for (const token of Object.keys(this.customTokens || {})) root.style.removeProperty(token.startsWith('--') ? token : `--${token}`);
    this.customTokens = customTokensObject && typeof customTokensObject === 'object' ? customTokensObject : {};

    // 2. Apply explicit custom token overrides
    if (this.customTokens) {
      Object.entries(this.customTokens).forEach(([token, val]) => {
        const key = token.startsWith('--') ? token : `--${token}`;
        root.style.setProperty(key, val);
      });
    }

    // 3. Persist theme preference to localStorage for instant boot hydration
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('universal-ui-theme', this.currentTheme);
      }
    } catch (e) {
      // Ignore storage access errors in restricted contexts
    }

    // 4. Dispatch global theme shift event across shadow roots
    window.dispatchEvent(
      new CustomEvent('universal-theme-change', {
        detail: {
          theme: this.currentTheme,
          tokens: this.customTokens
        },
        bubbles: true,
        composed: true,
      })
    );

    return this.currentTheme;
  },

  /**
   * Auto-restores stored theme preference from localStorage on page load.
   */
  initStoredTheme() {
    try {
      if (typeof localStorage !== 'undefined') {
        const savedTheme = localStorage.getItem('universal-ui-theme');
        if (savedTheme && THEME_PRESETS[savedTheme]) {
          this.setTheme(savedTheme);
        }
      }
    } catch (e) {
      // Ignore storage access errors
    }
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
      'universal-billing-funnel',
      'universal-ai-bridge',
      'ui-button', 'ui-input', 'ui-checkbox', 'ui-select', 'ui-dialog',
      'ui-tooltip', 'ui-toast', 'ui-tabs', 'ui-menu'
    ];
    return components.filter(tag => Boolean(customElements.get(tag)));
  }
};

// Bind to window object for global script / CDN usage
if (typeof window !== 'undefined') {
  window.UniversalUI = UniversalUI;
  // Initialize stored theme immediately on script boot
  UniversalUI.initStoredTheme();
}

export { UniversalUI };
