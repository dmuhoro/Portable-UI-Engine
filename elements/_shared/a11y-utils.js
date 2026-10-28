/**
 * Shared accessibility utilities for Universal UI components
 */

export function trapFocus(element) {
  const focusableElements = element.querySelectorAll('a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select');
  if (focusableElements.length === 0) return () => {};
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  const handleTabKey = (e) => {
    if (e.key !== 'Tab') return;
    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  };

  element.addEventListener('keydown', handleTabKey);
  return () => element.removeEventListener('keydown', handleTabKey);
}

export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function announce(message, priority = 'polite') {
  let announcer = document.getElementById('uui-announcer');
  if (!announcer) {
    announcer = document.createElement('div');
    announcer.id = 'uui-announcer';
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0';
    document.body.appendChild(announcer);
  }
  announcer.textContent = message;
}
