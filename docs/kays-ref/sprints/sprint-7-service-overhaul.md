# Sprint 7: Service Directory Overhaul & Executive-Grade Copy

## Timeline

- **Sprint:** 7
- **Focus:** Service content restructuring, premium copy upgrade, meta/SEO hardening

---

## Founder Narrative

Dr. Jackie needed her actual clinical offerings front and centre — BHRT, IV Nutritional Therapy, Chronic Disease Management, Functional Weight Management — not generic "wellness" copy that any spa could claim. Every paragraph was rewritten to sound like it came from a physician's pen: precise, evidence-grounded, commanding. The home page now reads as a clinical intake document, not a brochure.

---

## Technical Execution

### 1. Service Content Restructuring

- **`src/routes/services.tsx`**: Rewrote `treatments[]` array with 4 core protocols — each entry now carries physician-grade copy referencing specific diagnostic modalities (salivary cortisol mapping, mitochondrial support, gut microbiome assessment)
- **`src/routes/index.tsx`**: Replaced `focusAreas` array (old: generic wellness categories) with `treatments[]` array mirroring the services page — BHRT, IV Therapy, Chronic Disease, Weight Management. Each card links to `/services` for full protocol detail

### 2. Copy Upgrade — Executive-Grade Register

- All section headers and body copy across `index.tsx`, `services.tsx`, `our-story.tsx` rewritten to premium clinical tone
- Removed colloquial wellness language ("feel your best", "natural healing") — replaced with precision medical framing ("biomarker-driven prevention", "cellular health optimisation", "precision nutraceutical intervention")
- Hero headline ecosystem: "Precision medicine, engineered for your biology" / "From surviving to thriving"

### 3. Meta/SEO Hardening

- **`src/routes/__root.tsx`**: Replaced stale Unsplash `og:image` with premium clinical consultation photo (`photo-1576091160550-2173dba999ef`)
- Updated `title`, `description`, `og:title`, `og:description`, `twitter:title`, `twitter:description` to match executive-grade copy across all routes
- `og:image` + `twitter:image` both pointing to the new premium asset

### 4. Vercel Preset Configuration

- **`vite.config.ts`**: Added `nitro: { preset: "vercel" }` to switch from default Cloudflare preset to Vercel Serverless Functions (Node.js 20, Web API entry format)
- Auto-detected `nodejs20.x` runtime + `web` entry format (`vercel.web.mjs`)
- Zero-config — Vercel preset handles function routing, ISR, and streaming

### Files Modified

| File                      | Change                                          |
| ------------------------- | ----------------------------------------------- |
| `src/routes/services.tsx` | Full `treatments[]` rewrite, hero copy upgrade  |
| `src/routes/index.tsx`    | `focusAreas` → `treatments[]`, 4 protocol cards |
| `src/routes/__root.tsx`   | og:image + meta descriptions overhaul           |
| `vite.config.ts`          | Added `nitro: { preset: "vercel" }`             |
