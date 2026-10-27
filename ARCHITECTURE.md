# Daftari — Architecture

## Sync Coverage Matrix

| Entity | Dexie Table | Supabase Table | Push | Pull | RLS |
|---|---|---|---|---|---|
| Transactions | transactions | daftari_transactions | ✅ | ✅ | ✅ |
| Business profile | business | daftari_businesses | ✅ | ✅ | ✅ |
| Daily closes | daily_closes | daftari_daily_closes | ✅ | ✅ | ✅ |
| Customers | customers | daftari_customers | ✅ | ✅ | ✅ |
| Suppliers | suppliers | daftari_suppliers | ✅ | ✅ | ✅ |
| Purchase orders | purchase_orders | daftari_purchase_orders | ✅ | ✅ | ✅ |
| Stock adjustments | stock_adjustments | daftari_stock_adjustments | ✅ | ✅ | ✅ |
| STK Push requests | stk_requests | daftari_stk_requests | read-only | read-only | N/A (server-owned; Edge Functions are the only writer) |
| STK Push callbacks | stk_callbacks | daftari_stk_callbacks | N/A | N/A | N/A (service-role audit only) |
| Sync queue | sync_queue | (local only) | N/A | N/A | N/A |

Multi-device restore: all 7 entity types pull from Supabase on sign-in. Each table is
pulled independently, so one failure does not skip the rest; tables not yet deployed are
reported as `skipped` rather than silently omitted.
Push: syncAllTables() pushes all 7 entity types to Supabase when online. The device also
schedules a debounced write-through flush after each local write, so a device that is lost
mid-shift does not take that shift's sales with it.
