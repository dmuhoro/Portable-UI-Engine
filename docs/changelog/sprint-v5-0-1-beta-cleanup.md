# Sprint v5.0.1 — Beta Cleanup

**Release date:** 2026-07-19  
**Version:** `5.0.1`  
**Theme:** Closing all gaps for beta readiness

---

## What was built

### Data Safety
- **Complete cloud restore**: `pullFromSupabase` now restores all 7 entity types.
- **Silent catch blocks eliminated**: 6 critical `catch {}` blocks now log warnings.
- **Global unhandledrejection handler**: Added in `main.tsx`.
- **Category change confirmation**: Modal warns before clearing products.

### Validation & Integrity
- **Duplicate product name check**: Case-insensitive check with confirm dialog.
- **Duplicate supplier check**: Name and phone duplicate check.
- **Input maxLength enforcement**: All description/notes fields enforce `maxLength={200}`.
- **Empty state**: StockAdjustmentsScreen shows descriptive empty state.
- **Phone/email validation**: Supplier phone has `pattern` validation; email uses `type="email"`.

### User Feedback
- **Toast notification system**: `ToastProvider` + `useToast()` hook for success/error/info messages with auto-dismiss (4s). Wired into manual sync trigger.
- **Help/FAQ screen**: 6 accordion FAQs in Kiswahili/English. Accessible from Settings.

### Sync & Data Management
- **Manual sync trigger**: "Sync Now" button in Settings with toast feedback.
- **Background sync**: `registerBackgroundSync()` registered on online transition.
- **Local JSON backup**: `exportAllData()` downloads all 8 Dexie tables. "Export Backup" button in Settings.
- **Sync queue purge**: Synced entries deleted from queue. `getPendingCount()` export.

### Performance
- **Search debouncing**: 300ms on History, POS, Customers.
- **Virtualized customer list**: `react-virtuoso` for large customer lists.
- **Skeleton loaders**: Reusable `Skeleton` component, applied to CustomersScreen loading state.

### Accessibility
- **ARIA labels**: Added to back, search, scan, cart controls, filters, switchers across 5 screens.
- **Color-independent indicators**: "(Profit)"/"(Loss)" text labels on Dashboard profit cards.
- **Touch target sizes**: Cart qty buttons, back, scan now `min-w-[44px] min-h-[44px]`.
- **Screen reader announcements**: `aria-live="polite"` + `role="alert"` on DailyClose, Receipt, Toast.
- **Focus management**: `autoFocus` on receipt dismiss and customer picker modal.
- **Keyboard shortcuts**: n=new sale on Dashboard.

### Infrastructure
- **Desktop layout**: `max-w-lg mx-auto` constraint on AppShell.
- **CI/CD deploy job**: GitHub Actions now triggers Vercel deploy hook on push to main (after checks pass). PR previews via Vercel GitHub integration.
- **Unit tests**: `syncQueue.test.ts` — 54 tests total across 5 files.

---

## Files changed

| File | Change |
|------|--------|
| `CHANGELOG.md` | Added all v5.0.1 items |
| `package.json` | 5.0.0 → 5.0.1 |
| `tailwind.config.js` | Added `slide-up` animation keyframes |
| `docs/changelog/sprint-v5-0-1-beta-cleanup.md` | Updated |
| `src/components/Toast.tsx` | Created — toast system |
| `src/components/Skeleton.tsx` | Created — skeleton loader |
| `src/components/HelpScreen.tsx` | Created — FAQ accordion |
| `src/lib/backup.ts` | Created — JSON export utility |
| `src/lib/__tests__/syncQueue.test.ts` | Created — sync queue unit test |
| `src/App.tsx` | Wrapped with `<ToastProvider>` |
| `src/components/AppShell.tsx` | Added `help` view, `max-w-lg mx-auto`, keyboard shortcuts |
| `src/components/Receipt.tsx` | `aria-live`, `autoFocus` |
| `src/features/sync/syncQueue.ts` | Purge synced entries, `getPendingCount()`, `registerBackgroundSync()` |
| `src/hooks/useSync.ts` | Call `registerBackgroundSync()` on online |
| `src/features/close/DailyClose.tsx` | `role="alert"`, `aria-live` |
| `src/screens/SettingsScreen.tsx` | Sync Now button, Export Backup button, Help link |
| `src/screens/SuppliersScreen.tsx` | Phone `pattern`, `title` validation |
| `src/screens/DashboardScreen.tsx` | Color-independent profit/loss labels, POS shortcut |
| `src/screens/PosScreen.tsx` | Touch target sizes, `autoFocus` |
| `src/screens/CustomersScreen.tsx` | Skeleton loaders |
| `src/screens/ProductCatalogScreen.tsx` | Silent catch → warn, duplicate name check |
| `src/screens/PurchaseOrdersScreen.tsx` | maxLength on notes |
| `src/screens/StockAdjustmentsScreen.tsx` | Empty state text, ARIA label, maxLength |
| `src/features/sms/SMSParser.tsx` | Silent catch → warn |
| `src/features/transactions/RecordSale.tsx` | Silent catch → warn, maxLength |
| `src/features/transactions/RecordExpense.tsx` | maxLength on description |
| `src/features/transactions/RecordWithdrawal.tsx` | maxLength on note |
| `src/screens/OnboardingScreen.tsx` | Silent catch → warn |
| `src/screens/HistoryScreen.tsx` | Debounced search, ARIA labels |

---

## Verification

```bash
npm run typecheck    # ✅
npm run lint         # ✅ (0 errors, 6 pre-existing warnings)
npm run test:run     # ✅ (54 tests)
npm run build        # ✅
```
