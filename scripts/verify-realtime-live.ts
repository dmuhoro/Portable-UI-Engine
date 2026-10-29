/**
 * Live REALTIME deliverability verification (no browser).
 *
 * Proves what a SUBSCRIBED status alone cannot: that daftari_transactions is a
 * member of the supabase_realtime publication AND events actually stream. If
 * the table is not in the publication, the channel connects yet no event ever
 * arrives — exactly the silent-failure mode this probe exists to catch.
 *
 * It signs in with the REAL E2E account (never with anon), subscribes to
 * postgres_changes on its own rows, performs the same write the UI performs,
 * and asserts the event is DELIVERED over the channel before deleting it.
 * RLS stays fully in force; the probe only exercises the sanctioned path.
 *
 * Usage:
 *   VITE_SUPABASE_URL=https://<ref>.supabase.co \
 *   VITE_SUPABASE_ANON_KEY=<anon> \
 *   E2E_LIVE_EMAIL=... E2E_LIVE_PASSWORD=... \
 *   npx tsx scripts/verify-realtime-live.ts
 *
 * Exit codes: 0 = event delivered (publication active, RLS-scoped stream OK);
 *             1 = configuration missing (credential/env gap);
 *             2 = live failure (no delivery | RLS refusal | network error).
 */
import { createClient, type RealtimeChannel } from '@supabase/supabase-js';
import { randomUUID } from 'node:crypto';

const url = process.env.VITE_SUPABASE_URL;
const anon = process.env.VITE_SUPABASE_ANON_KEY;
const email = process.env.E2E_LIVE_EMAIL;
const password = process.env.E2E_LIVE_PASSWORD;

function fail(code: number, message: string): never {
  console.error(`[verify-realtime-live] ${message}`);
  process.exit(code);
}

if (!url || !anon || url.includes('localhost')) {
  fail(1, 'ERROR: VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY not set to a real project.');
}
if (!email || !password) {
  fail(1, 'ERROR: E2E_LIVE_EMAIL / E2E_LIVE_PASSWORD not set — needs the real E2E account.');
}

async function main(): Promise<void> {
  const client = createClient(url, anon);
  const { data: session, error: signInError } = await client.auth.signInWithPassword({ email, password });
  if (signInError || !session.user) {
    fail(2, `ERROR: sign-in failed (${signInError?.message ?? 'no user returned'}).`);
  }
  const userId = session.user.id;
  console.log(`[verify-realtime-live] signed in as ${email} (${userId})`);

  const localId = `realtime-probe-${randomUUID()}`;
  const DELIVERY_TIMEOUT_MS = 15_000;

  const delivered = new Promise<'insert' | 'timeout' | 'error' | 'foreign'>((resolve) => {
    let settled = false;
    const timer = setTimeout(() => { if (!settled) { settled = true; resolve('timeout'); } }, DELIVERY_TIMEOUT_MS);

    const channel: RealtimeChannel = client
      .channel('realtime-probe')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'daftari_transactions', filter: `user_id=eq.${userId}` },
        (payload) => {
          if (payload.new?.local_id !== localId) return; // ignore unrelated traffic
          clearTimeout(timer);
          if (!settled) { settled = true; resolve('insert'); }
        }
      );

    channel.subscribe((status, err) => {
      if (status === 'SUBSCRIBED') return;
      clearTimeout(timer);
      if (!settled) { settled = true; resolve('error'); }
      console.error(`[verify-realtime-live] channel status: ${status}${err ? ` (${err.message})` : ''}`);
    });
  });

  // Give the subscription a moment to attach before the write.
  await new Promise((r) => setTimeout(r, 1000));

  const { error: insertError } = await client.from('daftari_transactions').insert({
    local_id: localId,
    type: 'income',
    category: 'other',
    source: 'manual',
    amount: 1,
    recorded_at: new Date().toISOString(),
    user_id: userId,
    synced: 1,
  });

  if (insertError) {
    await client.removeAllChannels();
    fail(2, `ERROR: probe INSERT refused by RLS (${insertError.message}). Publication state unknown.`);
  }
  console.log('[verify-realtime-live] probe row written; awaiting realtime delivery…');

  const result = await delivered;
  await client.removeAllChannels();

  const { error: deleteError } = await client.from('daftari_transactions').delete().eq('local_id', localId);
  if (deleteError) {
    console.error(`[verify-realtime-live] WARN: probe cleanup failed (${deleteError.message}); row left under local_id ${localId}`);
  }

  if (result !== 'insert') {
    fail(2, `ERROR: no realtime delivery (${result}). Table is likely MISSING from the supabase_realtime publication — enable it in Database → Replication (see supabase/migrations/20260905210000_enable_realtime_tables.sql).`);
  }

  console.log('[verify-realtime-live] EVENT DELIVERED over postgres_changes — publication active, RLS-scoped stream OK.');
  process.exit(0);
}

void main();