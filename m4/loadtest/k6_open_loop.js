// Open-loop load test with k6.
//
// Requests arrive at a set rate, whether or not earlier ones have finished,
// like independent users on the internet. When the server cannot keep up,
// latency climbs and k6 reports dropped_iterations. That is the overload
// signal a closed-loop test hides (lecture 2).
//
// Edit ENDPOINTS and STAGES. {placeholders} are filled with ids from
// loadtest_ids.json, written by the seed scripts.
//
// Run:
//   k6 run -e BASE_URL=http://YOUR-APP:8000 k6_open_loop.js
//   k6 run -e BASE_URL=http://YOUR-APP:8000 --summary-export summary.json k6_open_loop.js

import http from 'k6/http';
import { check } from 'k6';

// =============================== CONFIG ===============================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// weight sets the traffic mix; name groups results per endpoint.
const ENDPOINTS = [
  { weight: 5, name: 'list posts (page 1)', path: '/posts?limit=20' },
  { weight: 2, name: 'list posts (deep page)', path: '/posts?limit=20&page={deep_page}' },
  { weight: 4, name: 'post detail', path: '/posts/{post_id}' },
  { weight: 2, name: 'user profile', path: '/users/{user_id}' },
  { weight: 1, name: "user's posts", path: '/users/{user_id}/posts' },
];

// Placeholder values that do not come from the seed data.
const EXTRA_VALUES = { deep_page: Array.from({ length: 1950 }, (_, i) => i + 50) };

// Arrival rate in requests per second, stepped up until the server breaks.
const STAGES = [
  { target: 20, duration: '1m' },   // warm-up (ignore these results)
  { target: 50, duration: '2m' },
  { target: 100, duration: '2m' },
  { target: 200, duration: '2m' },
  { target: 400, duration: '2m' },
];

// ============================ END CONFIG ==============================

const VALUES = Object.assign(JSON.parse(open('./loadtest_ids.json')), EXTRA_VALUES);
const TOTAL_WEIGHT = ENDPOINTS.reduce((sum, e) => sum + e.weight, 0);
const HEADERS = __ENV.API_TOKEN ? { Authorization: `Bearer ${__ENV.API_TOKEN}` } : {};

export const options = {
  scenarios: {
    open_loop: {
      executor: 'ramping-arrival-rate',
      startRate: 5,
      timeUnit: '1s',
      preAllocatedVUs: 50,     // virtual users ready to send requests
      maxVUs: 1000,            // if all are busy waiting, k6 drops iterations
      stages: STAGES,
    },
  },
  // Pass/fail lines in the summary. Adjust to your own goals.
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500', 'p(99)<1500'],
  },
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
};

function pickEndpoint() {
  let r = Math.random() * TOTAL_WEIGHT;
  for (const e of ENDPOINTS) {
    r -= e.weight;
    if (r < 0) return e;
  }
  return ENDPOINTS[ENDPOINTS.length - 1];
}

function fill(path) {
  return path.replace(/\{(\w+)\}/g, (_, key) => {
    const list = VALUES[key];
    return list[Math.floor(Math.random() * list.length)];
  });
}

export default function () {
  const e = pickEndpoint();
  const res = http.get(`${BASE_URL}${fill(e.path)}`, { headers: HEADERS, tags: { name: e.name } });
  check(res, { 'status is 2xx': (r) => r.status >= 200 && r.status < 300 });
}
