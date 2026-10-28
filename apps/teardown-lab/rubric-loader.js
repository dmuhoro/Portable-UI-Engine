export default async function loadRubric() {
  // Attempt to load rubric-v1.json via fetch (works in browsers, Node with --experimental-fetch)
  try {
    const res = await fetch(new URL('./rubric-v1.json', import.meta.url));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rubric = await res.json();
    console.log('Rubric loaded:', rubric.name);
    return rubric;
  } catch (e) {
    // Fallback: Node environments without experimental fetch support
    // Return the rubric structure inline (will be overridden by bundler or AI Studio preview)
    console.warn('Rubric fetch failed (expected in some Node versions), using inline rubric');
    return {
      name: 'Rubric v1',
      version: '1.0.0',
      criteria: [
        { id: 'visual_hierarchy', name: 'Visual Hierarchy & Layout', weight: 1 },
        { id: 'typography', name: 'Typography Scale & Rhythm', weight: 1 },
        { id: 'color_contrast', name: 'Color & Contrast (WCAG AA)', weight: 1 },
        { id: 'spacing', name: 'Spacing System Consistency', weight: 1 },
        { id: 'interaction_states', name: 'Interaction States', weight: 1 },
        { id: 'motion', name: 'Motion (purposeful, reduced-motion)', weight: 1 },
        { id: 'keyboard', name: 'Keyboard Operability & Focus', weight: 1 },
        { id: 'a11y_semantics', name: 'Screen-reader Semantics', weight: 1 },
        { id: 'responsive', name: 'Responsiveness (320,768,1280)', weight: 1 },
        { id: 'tokens', name: 'Theming & Token Discipline', weight: 1 },
        { id: 'api_clarity', name: 'API Contract Clarity', weight: 1 },
        { id: 'performance', name: 'Performance & Bundle Weight', weight: 1 }
      ]
    };
  }
}
