# Sprint 1 — MVP Foundation

**Date:** 2026-06-18  
**Version:** 1.0.0  
**Status:** Completed ✅

## Overview
Initial launch of Daftari as an offline-first PWA for Kenya's informal vendors. Core transaction engine, M-Pesa SMS parsing, dashboards, and offline sync infrastructure.

## Features Delivered
- Auth: email + password sign up and sign in via Supabase
- Transaction engine: income, expense, withdrawal recording
- Fuliza debt tracking (debt_taken + debt_repaid) with alert card
- Quick-add: configurable product chips (chapati KES 20 default)
- M-Pesa SMS parser: 3 Safaricom patterns + fallback (fully offline)
- Today dashboard: profit hero card, revenue, expenses, cash available
- Weekly dashboard: 7-day Recharts bar chart, best day, week totals
- Transaction history: date-grouped, pull-to-refresh
- Daily close flow: 8pm EAT bottom sheet with day P&L summary
- Offline-first: full operation on airplane mode via Dexie.js IndexedDB
- Background sync: queue flushes to Supabase on connectivity restore
- Kiswahili + English language toggle (Kiswahili default)
- PWA: installable on Android Chrome, service worker, offline fallback
- Supabase RLS on all tables (owner_id isolation)

## Files Created
- `src/lib/db.ts` — Dexie schema (transactions, sync_queue, business, daily_closes)
- `src/lib/store.ts` — Zustand store (language, business, transactions)
- `src/lib/supabase.ts` — Supabase client
- `src/features/sms/parseMpesa.ts` — SMS parser (3 patterns + fallback)
- `src/features/sync/syncQueue.ts` — Offline sync queue
- `src/screens/` — Auth, Dashboard, Add, History, Settings screens
- `src/features/transactions/` — RecordSale, RecordExpense, RecordWithdrawal, RecordFulizaDebt, RecordFulizaRepaid
- `src/hooks/useTranslation.ts` — i18n system
- `src/i18n/` — sw.json (92 keys), en.json (92 keys)

## Breaking Changes
- N/A — initial release

## Next
Sprint 2: Elite Engineering Foundation
