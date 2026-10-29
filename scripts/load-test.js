// Daftari — k6 load test (synthetic load against the PRODUCTION deployment).
//
// Requires the k6 binary (https://grafana.com/k6):  npm run test:load
// Targets the canonical live URL (daftari-amber.vercel.app) which serves the
// latest main build. Throttled-entry ramp avoids hammering a shared dev tier.
//
// NOTE: this drives the PUBLIC static shell + PWA bundle only. Supabase-auth
// mutating endpoints (signup, subscribe) are NOT exercised — synthetic load
// against auth/sync tables would pollute real user data.

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },  // ramp up
    { duration: '60s', target: 50 },  // steady
    { duration: '30s', target: 100 }, // peak
    { duration: '30s', target: 0 },   // cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],       // 95th percentile under 2s
    http_req_failed: ['rate<0.05'],          // <5% errors
  },
};

const BASE_URL = 'https://daftari-amber.vercel.app';

export default function () {
  const res = http.get(BASE_URL, { tags: { name: 'landing' } });
  check(res, {
    'landing returns 200': (r) => r.status === 200,
    'landing is the PWA shell': (r) => r.body.includes('Daftari'),
  });
  sleep(1);
}