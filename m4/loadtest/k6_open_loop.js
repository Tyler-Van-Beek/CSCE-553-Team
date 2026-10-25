// Open-loop load test with k6.
//
// Requests arrive at a target rate regardless of whether earlier requests
// have finished. This helps reveal overload because latency may increase
// and k6 may report dropped_iterations when the system cannot keep up.
//
// Run:
//   k6 run -e BASE_URL=http://YOUR-APP -e API_TOKEN=YOUR_TOKEN k6_open_loop.js
//
// Save summary:
//   k6 run -e BASE_URL=http://YOUR-APP -e API_TOKEN=YOUR_TOKEN \
//     --summary-export summary.json k6_open_loop.js

import http from 'k6/http';
import { check } from 'k6';

// =============================== CONFIG ===============================

// Azure application URL is supplied through the BASE_URL environment variable.
// Falls back to local Django if BASE_URL is not supplied.
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

// Controlled 50/50 comparison between deep OFFSET pagination
// and deep keyset pagination for the same hot event.
const ENDPOINTS = [
  {
    weight: 1,
    name: 'hot event offset deep',
    path: '/api/events/2464/registrations?page=251',
  },
  {
    weight: 1,
    name: 'hot event keyset deep',
    path: '/api/events/2464/registrations-keyset?after=133019',
  },
];

// No placeholders are needed for this controlled experiment.
const EXTRA_VALUES = {};

// Open-loop arrival rate in requests per second.
// Start gently and increase traffic step by step.
const STAGES = [
  { target: 2, duration: '1m' },
  { target: 5, duration: '2m' },
  { target: 10, duration: '2m' },
  { target: 20, duration: '2m' },
  { target: 40, duration: '2m' },
];

// ============================ END CONFIG ==============================

// Kept from the professor's script structure.
// loadtest_ids.json is still read so this file can later be extended
// with event/user placeholders if needed.
const VALUES = Object.assign(
  JSON.parse(open('./loadtest_ids.json')),
  EXTRA_VALUES
);

const TOTAL_WEIGHT = ENDPOINTS.reduce(
  (sum, endpoint) => sum + endpoint.weight,
  0
);

// Our Django REST Framework API uses:
// Authorization: Token <token>
const HEADERS = __ENV.API_TOKEN
  ? { Authorization: `Token ${__ENV.API_TOKEN}` }
  : {};

export const options = {
  scenarios: {
    open_loop: {
      executor: 'ramping-arrival-rate',

      // Begin at 1 request per second.
      startRate: 1,

      // All stage targets are requests per second.
      timeUnit: '1s',

      // Pre-create enough VUs so k6 can generate requests without
      // constantly allocating new virtual users.
      preAllocatedVUs: 50,

      // Limit VUs because the load-generator VM is small.
      maxVUs: 200,

      stages: STAGES,
    },
  },

  // These are reference thresholds.
  // A failed threshold does not automatically mean the application is broken;
  // it helps us identify when latency/error goals are exceeded.
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: [
      'p(95)<500',
      'p(99)<1500',
    ],
  },

  // Metrics we want displayed in the final k6 summary.
  summaryTrendStats: [
    'avg',
    'med',
    'p(95)',
    'p(99)',
    'max',
  ],
};


// Randomly choose an endpoint according to its weight.
function pickEndpoint() {
  let randomValue = Math.random() * TOTAL_WEIGHT;

  for (const endpoint of ENDPOINTS) {
    randomValue -= endpoint.weight;

    if (randomValue < 0) {
      return endpoint;
    }
  }

  return ENDPOINTS[ENDPOINTS.length - 1];
}


// Replace placeholders such as {event_id} if we add them later.
// For the current experiment, our paths do not contain placeholders.
function fill(path) {
  return path.replace(/\{(\w+)\}/g, (_, key) => {
    const values = VALUES[key];

    if (!values || values.length === 0) {
      throw new Error(`No values available for placeholder: ${key}`);
    }

    return values[Math.floor(Math.random() * values.length)];
  });
}


export default function () {
  const endpoint = pickEndpoint();

  const response = http.get(
    `${BASE_URL}${fill(endpoint.path)}`,
    {
      headers: HEADERS,

      // Groups statistics by logical endpoint instead of the full URL.
      tags: {
        name: endpoint.name,
      },
    }
  );

  check(response, {
    'status is 2xx': (res) =>
      res.status >= 200 && res.status < 300,
  });
}
