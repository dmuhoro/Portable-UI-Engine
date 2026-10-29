# Sprint 6: Premium Asset Overhaul & Visual Identity Hardening

## Timeline

- **Sprint:** 6
- **Focus:** Visual asset replacement, image pipeline refactoring, brand coherence

---

## Founder Narrative

The site was still carrying generic Unsplash imagery — Western clinics, anonymous hospital corridors. For Dr. Jackie's Kenyan executive clientele, every visual touchpoint needed to reflect _African wellness, clinical precision, and luxury_. We replaced each placeholder with imagery that mirrors her actual patient demographic: African professionals, serene Nairobi wellness spaces, multi-generational family care.

---

## Technical Execution

### 1. Image Asset Pipeline — Full Replacement

- **`src/routes/index.tsx`**: Replaced all 4 Unsplash references (hero, drJackie, CTA background) with premium African wellness stock — warm clinical consultation scenes, African female physicians, Nairobi-appropriate imagery
- **`src/routes/our-story.tsx`**: Replaced founder image and hero background with culturally relevant medical photography
- **`src/components/site/HeroCarousel.tsx`**: Introduced `bgImages[]` array (3 rotating backgrounds) with Savannah Olive overlay gradient for cohesive brand lockup. Each slide now has a dedicated complementary background image tied to its messaging

### 2. HeroCarousel Structural Enhancement

- Added `bgImages` typed string array alongside existing slide data
- Each slide's background rendered via inline `backgroundImage` style with `linear-gradient` overlay (`from-foreground/70 to-foreground/40`) to maintain text legibility across varying image tones
- Preserved existing 6.5s auto-rotate, glass caption cards, and CTA buttons

### 3. Design Token Adherence

All new imagery graded behind the established palette:

- Savannah Olive (`#1E352F`) overlay gradients
- Terracotta `--accent` accent on tag badges
- Glass panel (`glass` utility) overlays ensure readability on any background image

### Files Modified

| File                                   | Change                                             |
| -------------------------------------- | -------------------------------------------------- |
| `src/routes/index.tsx`                 | 4 image URLs replaced + unused imports cleaned     |
| `src/routes/our-story.tsx`             | Hero + founder images replaced                     |
| `src/components/site/HeroCarousel.tsx` | `bgImages[]` array, per-slide background rendering |
