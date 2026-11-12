
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = (__ENV.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

const TEST_CASES = {
  zero: {
    path: '/api/search?q=xyznonexistent987',
    expected: 0,
  },
  arts: {
    path: '/api/search?q=monitoring&category=Arts',
    expected: 2,
  },
  tech: {
    path: '/api/search?q=monitoring&category=Tech',
    expected: 5,
  },
  community: {
    path: '/api/search?q=monitoring&category=Community',
    expected: 17,
  },
  many: {
    path: '/api/search?q=monitoring',
    expected: 20, // First page of 120 matching events
  },
};

const CASE_NAME = __ENV.SEARCH_CASE || 'tech';
const QUICK_TEST = __ENV.QUICK_TEST === 'true';
const testCase = TEST_CASES[CASE_NAME];

if (!testCase) {
  throw new Error(`Unknown SEARCH_CASE: ${CASE_NAME}`);
}

export const options = __ENV.SMOKE_TEST === 'true'
  ? {
      vus: 1,
      iterations: 1,
    }
  : QUICK_TEST
  ? {
      scenarios: {
        quick_test: {
          executor: 'constant-arrival-rate',
          rate: 2,
          timeUnit: '1s',
          duration: '30s',
          preAllocatedVUs: 5,
          maxVUs: 20,
        },
      },
      summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
    }
  : {
      // Keep your existing full-load options here
  scenarios: {
    search_load: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 20,
      maxVUs: 100,
      stages: [
        { target: 2, duration: '1m' },
        { target: 5, duration: '2m' },
        { target: 10, duration: '2m' },
        { target: 20, duration: '2m' },
        { target: 40, duration: '2m' },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500', 'p(99)<1500'],
  },
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
};

export default function () {
  const response = http.get(`${BASE_URL}${testCase.path}`, {
    headers: {
      Authorization: `Token ${__ENV.API_TOKEN || ''}`,
    },
    tags: {
      name: CASE_NAME,
    },
  })
  if (response.status !== 200) {
  console.log(
    `Search case: ${CASE_NAME}, ` +
    `HTTP status: ${response.status}, ` +
    `Duration: ${response.timings.duration}ms, ` +
    `Body: ${String(response.body || '').slice(0, 200)}`
  );
};

  check(response, {
    'status is 200': (r) => r.status === 200,
    'expected first-page results': (r) => {
      if (r.status !== 200) return false;
      try {
        const body = r.json();
        return body.results.length === testCase.expected;
      } catch {
        return false;
      }
    },
  });
}
