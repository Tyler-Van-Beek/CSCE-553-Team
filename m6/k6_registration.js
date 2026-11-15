import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';

const token = __ENV.M6_K6_TOKEN;
const eventIds = (__ENV.M6_K6_EVENT_IDS || '').split(',').map(Number);
const rate = Number(__ENV.M6_K6_RATE || '2');

if (!token || eventIds.length < rate * 15 + 1 || eventIds.some(id => !Number.isInteger(id) || id <= 0)) {
  throw new Error('Set the local login token and supply enough fresh event IDs for the run.');
}

export const options = {
  scenarios: {
    register: {
      executor: 'constant-arrival-rate',
      rate,
      timeUnit: '1s',
      duration: '15s',
      preAllocatedVUs: 10,
    },
  },
  thresholds: {
    checks: ['rate==1'],
    dropped_iterations: ['count==0'],
  },
};

export default function () {
  const eventId = eventIds[exec.scenario.iterationInTest];
  const response = http.post(
    'http://127.0.0.1:8006/api/registrations',
    JSON.stringify({ EventID: eventId }),
    {
      headers: {
        Authorization: `Token ${token}`,
        'Content-Type': 'application/json',
      },
    },
  );

  check(response, { 'registration created (201)': r => r.status === 201 });
}