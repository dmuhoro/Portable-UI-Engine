export default async function loadRubric() {
  // Try fetch first (works in browsers and Node with --experimental-fetch)
  try {
    const res = await fetch(new URL('../../audit/rubric-v1.json', import.meta.url));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rubric = await res.json();
    console.log('Rubric loaded:', rubric.name);
    return rubric;
  } catch (e) {
    // Fallback: manual JSON import for Node environments
    // In Node, use: const rubric = require('../../audit/rubric-v1.json');
    // For browser, fetch above handles it
    console.warn('Could not load rubric via fetch, using fallback');
    return { name: 'Rubric v1', version: '1.0.0', criteria: [] };
  }
}
