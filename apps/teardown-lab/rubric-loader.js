export default async function loadRubric() {
  // Load rubric from same directory
  try {
    const rubric = await import('./rubric-v1.json', { assert: { type: 'json' } });
    console.log('Rubric loaded:', rubric.name);
    return rubric.default;
  } catch (e) {
    console.warn('Could not load rubric, using empty fallback', e.message);
    return { name: 'Rubric v1', version: '1.0.0', criteria: [] };
  }
}
