# Daftari — User Guide

Daftari is an offline-first business ledger for Kenyan SMEs. This is the **user** manual — how a
duka owner uses Daftari day-to-day.

- Are you the person who **runs the deployed system**? → `docs/operator-guide.md`
- Are you a **programmer extending the code**? → `docs/programmer-guide.md`

Default language is Kiswahili; you can switch to English any time from the landing screen, or
under Settings → Appearance.

---

## 1. Get started

1. Open the app (installed PWA or the hosted URL).
2. Tap **Anza Bure** / **Start free**.
3. Complete the short onboarding quiz — a few quick questions about your business type and
   money-tracking habits — then enter your business name and subcategory.
4. Grant notifications if you'd like a reminder to close your day; skip if you prefer not to.

Your business is created on-device (IndexedDB) immediately, and in the cloud once you're back
online.

## 2. Record a sale

- On the **Dashboard**, tap **+** (the add button) → **Sale**.
- Enter the amount, tap the category, choose the payment method (M-Pesa, Till, Cash, …),
  optionally pick a customer and product, then save.
- Every sale gets an automatic receipt number (`REC-YYMMDD-XXXX`).

Or paste an M-Pesa message under **M-Pesa** — Daftari fills amount, sender, and payment method
for you.

## 3. Record expenses & withdrawals

- **Expense** and **Withdrawal** work the same way as a sale. Withdrawals are flagged so you can
  separate owner cash-outs from business expenses.

## 4. Track customers

- Customers are detected automatically from M-Pesa senders. Open **Customers** from Settings →
  Wateja to view each customer's history, loyalty points, and outstanding debt.
- Send a WhatsApp debt reminder directly from a customer's detail screen.

## 5. Daily close

- After 8 pm East Africa Time, Daftari reminds you to close the day.
- Close shows your day's revenue, expenses, and profit. Closing locks the day into your records.

## 6. Inventory (products)

- From **Settings → My Products**, add products with price, cost price, and stock levels.
- Low-stock alerts appear on your dashboard; restock from Inventory Management.
- **Quick POS mode** opens a full-screen cashier grid for fast checkout.

## 7. Growth Engine

- **Growth Engine** turns your daily activity into shareable WhatsApp stories — daily milestone,
  debt-recovery victory, or founder update — in one tap.

## 8. Second Brain

- From **Settings → Business Tools → Second Brain**, capture quick thoughts into your DataBank
  vault. Configure the vault URL + token there first (off by default).

## 9. Sync & backup

- Daftari works fully offline. When you're online, the sync icon in the header shows queue
  status; pending items retry automatically with backoff.
- **Settings → Data & Reports → Export Backup** downloads every table as one JSON file — keep a
  copy on your phone for safety.

## 10. Multi-business

- From **Settings → Business Tools**, add another business and switch between them from the
  dashboard dropdown. Each business keeps its own ledger and is synced separately.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Sales not uploading | Wait for the sync icon to clear, or tap **Sync Now** in Settings → Data & Reports. |
| Can't install as an app | Use Chrome on Android (Add to Home Screen) or Safari Share → Add to Home Screen on iOS. |
| Missing M-Pesa detection | The SMS screen parses pasted text — paste the full SMS, not a screenshot. |
| Forgot where a feature is | Open **Settings** and read the section titles — everything is grouped (Records, Money, Inventory, Business Tools). |

---

See `docs/deployment-runbook.md` for the engineering release process and `docs/offline-verified.md`
for evidence of the verified offline behavior.