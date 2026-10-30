// @ts-nocheck
'use client';

import './engine-loader';

export default function Page() {
  return (
    <main>
      <h1>Portable UI Engine — Next.js consumer</h1>
      <p>Client-only registration of Portable UI Engine primitives.</p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <ui-button variant="primary">Save</ui-button>
        <ui-input label="Workspace" name="workspace" />
      </div>
      <ui-dialog label="Confirm">
        <p>Dialog content</p>
      </ui-dialog>
      <ui-tabs></ui-tabs>
    </main>
  );
}
