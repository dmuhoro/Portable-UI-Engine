import { EngineLoader } from './engine-loader';

export default function Page() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <EngineLoader />
      <h1>Next.js consumer</h1>
      <p>Client-only registration of Portable UI Engine primitives.</p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <ui-button variant="primary">Save</ui-button>
        <ui-input label="Workspace" name="workspace" />
      </div>
      <ui-dialog label="Confirm">
        <p>Dialog content projected from React.</p>
      </ui-dialog>
      <ui-tabs />
    </main>
  );
}
