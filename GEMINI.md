# Daftari — Business Ledger App

## Tech Stack
- React 18 + Vite + TypeScript
- Zustand (state management)
- Dexie (IndexedDB for offline)
- Supabase (auth + sync)
- Tailwind CSS (styling)
- recharts (charts)
- lucide-react (icons)

## Architecture
- Offline-first: all data writes go to Dexie first, then sync queue → Supabase
- Zustand store persisted to localStorage (language, business, lastCloseDate)
- Transactions table in Dexie = source of truth for UI
- Sync queue in Dexie processes upserts/deletes when online

## Key Files
- `src/lib/store.ts` — Zustand store (business, transactions, language)
- `src/lib/db.ts` — Dexie schema (version 3)
- `src/features/sync/syncQueue.ts` — offline sync queue
- `src/features/sms/parseMpesa.ts` — M-Pesa SMS parser (patterns A-G)
- `src/screens/*.tsx` — all screens
- `src/components/AppShell.tsx` — root shell with bottom nav + view routing

## Business Data Model
- Business has: id, name, owner_name, currency, category, subcategory, payment_methods (string[]), products (Array<{id, name, price, unit}>)
- Transaction has: local_id, type (income/expense/withdrawal/debt_taken/debt_repaid), category, source (manual/sms), amount, description, recorded_at, synced, user_id, mpesa_code, mpesa_sender, payment_method

## Categories (7)
food_hospitality, retail_shop, services, health_beauty, transport_logistics, agriculture, artisan_construction

## Building
```bash
npm run dev      # dev server
npm run build    # production build
npm run typecheck  # TypeScript check
npm run lint     # ESLint
```

## Translation Keys
All UI text uses `useTranslation` hook with keys in `src/i18n/sw.json` and `src/i18n/en.json`. Always add keys to both files before using in UI.
