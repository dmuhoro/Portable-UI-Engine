'use client';

import './engine-loader';

export default function Page() {
  return (
    <main>
      <h1>Portable UI Engine — Next.js consumer</h1>
      <p>Client-only registration of Portable UI Engine primitives.</p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        {/* @ts-ignore */}
        <ui-button variant="primary">Save</ui-button>
        {/* @ts-ignore */}
        <ui-input label="Workspace" name="workspace" />
      </div>
      {/* @ts-ignore */}
      <ui-dialog label="Confirm">
        {/* @ts-ignore */}
        <p>Dialog content</p>
      </ui-dialog>
      {/* @ts-ignore */}
      <ui-tabs></ui-tabs>
    </main>
  );
}
