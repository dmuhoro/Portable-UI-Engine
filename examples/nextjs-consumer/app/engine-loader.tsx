'use client';

import { useEffect } from 'react';

/**
 * Registers Portable UI Engine custom elements on the client only.
 * Importing the engine during SSR throws because Custom Elements / Shadow DOM
 * are browser APIs.
 */
export function EngineLoader() {
  useEffect(() => {
    void import('@universal-ui/engine');
  }, []);
  return null;
}
