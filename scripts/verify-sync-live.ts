/**
 * Live sync verification without a browser.
 *
 * Loads the app's OWN bearer path (createClient with VITE_* env through the same
 * lib/supabase.ts defaults) and exercises exactly the round-trip the UI performs:
 *   anon auth.signUp(placeholder) -> signing in -> upserting a scrap-record to
 *   daftari_transactions -> reading it back filtered by user_id -> deleting it.
 *
 * This deliberately exercises the real network path (REST + RLS), NOT a mock of
 * supabase-js. Anonymous signup is disabled on daftari.app supersets, so this
 * consumes an ephemeral throwaway account on the SAME anon key the app ships —
 * no service-role key is required and no credentials leave the machine.
 *
 * Usage:
 *   VITE_SUPABASE_URL=https://<ref>.supabase.co \
 *   VITE_SUPABASE_ANON_KEY=<anon> \
 *   VITE_VERIFY=true \
 *   node scripts/verify-sync-live.ts
 *
 * Exit codes: 0 = full write/read/delete round-trip proven; 1 = configuration
 * missing (the build is NOT wired); 2 = a live round-trip failure.
 */
import { createClient } from '@supabase/supabase-js';

  const url = process.env.VITE_SUPABASE_URL;
  const anon = process.env.VITE_SUPABASE_ANON_KEY;

  if (!url || !anon || url.includes('localhost')) {
    console.error('[verify-sync-live] ERROR: VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY not set to a real project. The shipped build is NOT wired to Supabase.');
    process.exit(1);
  }
  if (process.env.VITE_VERIFY !== 'true') {
    console.error('[verify-sync-live] ERROR: refusing destructive proof without VITE_VERIFY=true (this creates + deletes a throwaway record).');
    process.exit(2);
  }

  const client = createClient(url, anon);

  const email = `verify-${Date.now()}@mail.daftari.verify`;
  const password = `Verify-${Date.now()}-aA1!`;

  const table = 'daftari_transactions';
  const localId = `verify-${Date.now()}`;
  const scrap = {
    local_id: localId,
    type: 'expense',
    category: 'other',
    source: 'manual',
    amount: 1,
    description: 'live-sync-verification-scrap',
    recorded_at: new Date().toISOString(),
    synced: 1,
  };

  try {
    const { data: signUp, error: signUpErr } = await client.auth.signUp({ email, password });
    if (signUpErr) throw signUpErr;
    const userId = signUp.user?.id;
    if (!userId) throw new Error('signUp returned no user id');

    const { error: signInErr } = await client.auth.signInWithPassword({ email, password });
    if (signInErr) throw signInErr;

    const { error: upsertErr } = await client.from(table).upsert(scrap, { onConflict: 'local_id' });
    if (upsertErr) throw upsertErr;

    const { data: rows, error: readErr } = await client
      .from(table)
      .select('local_id, user_id')
      .eq('local_id', localId);
    if (readErr) throw readErr;

    const mine = (rows || []).find((r) => String(r.user_id) === String(userId));
    if (!mine) throw new Error('RLS read-back returned the record but not for this user');

    const { error: delErr } = await client.from(table).delete().eq('local_id', localId);
    if (delErr) throw delErr;

    console.log('[verify-sync-live] PASS: url okay, anon signup+signin ok, upsert ok, RLS-filtered read-back ok, cleanup delete ok.');
    console.log(`[verify-sync-live] round-trip local_id=${localId} on authentic anon path.`);
    process.exit(0);
  } catch (cause) {
    const msg = cause instanceof Error ? cause.message : String(cause);
    console.error(`[verify-sync-live] FAIL: ${msg}`);
    process.exit(2);
  }
