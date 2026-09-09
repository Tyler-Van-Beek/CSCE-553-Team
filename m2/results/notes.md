# M2 Measurement Notes

All timestamps use UTC-05:00 unless otherwise stated.

## Hosted cold start

- Series: H
- Timestamp: 2026-09-08 00:26:03 -05:00
- Inactivity before request: At least 15 minutes
- Method and path: GET /health/
- HTTP status: 200
- Wall-clock latency: 0.321745 seconds (321.745 ms)
- Response size: 16 bytes
- Observation: No long Render wake-up delay was observed during this cold-start attempt.
- Command:

  ```powershell
  curl.exe -sS -o NUL -w "http_code=%{http_code} total_s=%{time_total} bytes=%{size_download}`n" "$BASE_H/health/"

### Second cold-start attempt

- Timestamp: 2026-09-08 10:04:20 -05:00
- Inactivity before request: At least 15 minutes
- Method and path: GET /health/
- HTTP status: 200
- Wall-clock latency: 0.432801 seconds (432.801 ms)
- Response size: 16 bytes
- Observation: A second cold-start attempt also showed no long Render wake-up delay.

## Data preparation

- The hosted event list initially contained 6 events with a response size of 1,131 bytes.
- One validation event was created successfully.
- During the next sequential seeding attempt, events 1 through 9 succeeded, but request 10 returned HTTP 500.
- The seeding helper stopped immediately after the failure.
- A later health request returned HTTP 200, and `GET /api/events` returned HTTP 200.
- After recovery, the database contained 16 events and the event-list response size was 3,185 bytes.
- This occurred during sequential data preparation, not during a controlled M2 load-test stage. Therefore, it is recorded as a preparation confound and is not included in the performance CSV results.

## Hosted database connection failure during preparation

- Timestamp: 2026-09-08 16:56:25 UTC
- Phase: Sequential data preparation, before the controlled load sweep
- Supabase Supavisor error: EMAXCONNSESSION
- Session-mode pool limit: 15 clients
- Observed effect: POST /api/events returned HTTP 500, followed by repeated HTTP 500 responses from GET /api/events.
- GET /health/ continued returning HTTP 200 because the health endpoint does not perform a database query.
- Database inspection after the failure showed:
  - Event count: 35
  - Total pg_stat_activity rows: 28
  - Idle: 20
  - Active: 1
  - State unavailable/null: 7
- Interpretation: The application remained running, but database-backed requests failed because the session-mode connection pool was exhausted.
- This was not a controlled M2 stage, so it is recorded as a preparation confound rather than included in summary.csv.

- Supabase reported EMAXCONNSESSION with a session pool limit of 15.
- Approximately 30 minutes after requests stopped, Supavisor still showed 15 idle connections.
- Restarting the original Render service did not restore database-backed requests.
- After restart, GET /health/ returned HTTP 200 while GET /api/events continued returning HTTP 500.


## Replacement hosted environment H2

Because the original M1 hosted service continued returning HTTP 500 for database-backed event requests after a restart, a replacement hosted environment was created using the same GitHub application code and architecture.

- Environment label: H2
- API host: https://lagniappe-priya-m2.onrender.com
- Hosting: Render free web service
- Database: Supabase PostgreSQL
- Compute: 0.1 CPU and 512 MB RAM

### H2 cold-start measurement

- Timestamp: 2026-09-08 14:40:38 -05:00
- Idle condition: Render free service had spun down
- Method and path: GET /health/
- HTTP status: 200
- Wall-clock latency: 46.482452 seconds (46,482.452 ms)
- Response size: 16 bytes
- Observation: The first request took approximately 46.5 seconds while the Render service started. This result is kept separate from all warm steady-state measurements.

### H2 warm health check

- Timestamp: 2026-09-08 14:47:16 -05:00
- Method and path: GET /health/
- HTTP status: 200
- Wall-clock latency: 0.265976 seconds (265.976 ms)
- Response size: 16 bytes
- Comparison: The 46.482452-second cold request was approximately 175 times slower than this warm request.

### H2 initial API verification

- API login returned HTTP 200 and a valid DRF authentication token.
- Authenticated GET /api/events returned HTTP 200.
- Warm event-list latency: 0.280022 seconds (280.022 ms)
- Initial event count: 9
- Initial response size: 1,858 bytes
- Observation: H2 could access its PostgreSQL database successfully, unlike the original H1 service, which continued returning HTTP 500 for database-backed requests.
- Decision: H2 will be used as the controlled hosted environment unless the original H1 environment is repaired in time.

### H2 data preparation completed

- Initial event count: 9
- Sequential synthetic events added: 41
- Final event count: 50
- Final GET /api/events response size: 10,500 bytes
- Verification request status: HTTP 200
- Verification request latency: 0.412142 seconds
- Supavisor idle connections before seeding: 2
- Supavisor idle connections after seeding: 1
- Observation: All 41 sequential writes succeeded, and H2 remained below the 15-session limit. The event list is now stable and will not be changed during the read-path sweep.

### Hosted API metric limitation

- Render application CPU and memory graphs were not available on the free compute plan.
- Render required upgrading to a paid plan to view these application metrics.
- The team did not upgrade because M2 prohibits paying for a larger Render instance to improve or observe the hosted baseline.
- API CPU and memory are therefore recorded as not observable for H2.
- Hosted resource evidence will use Supabase database connections and any available database CPU or database resource metrics.
- Local series L will capture Django process CPU and memory using Windows Task Manager.

## H2 health control — concurrency 2

- Start: 2026-09-08 20:57:10 -05:00
- Endpoint: `GET /health/`
- Authentication: none
- Warm-up: 10 seconds
- Measurement window: 60 seconds
- Concurrency: 2
- Attempts: 908
- Successes: 908
- Errors: 0
- Successful throughput: 15.114 requests/second
- p50: 127.70 ms
- p95: 164.97 ms
- p99: 223.52 ms
- Maximum: 1142.21 ms
- Error rate: 0%
- Mid-stage database connections: 16 total; Supavisor 1 idle and 0 active
- Interpretation: The lightweight health endpoint was healthy. It provides a control measurement for comparison with the database-backed events endpoint.

## H2 authenticated event read — concurrency 1

- Start: 2026-09-08 21:19:58 -05:00
- Endpoint: `GET /api/events`
- Authentication: Django token
- Dataset: 50 events
- Response payload: 10,500 bytes
- Warm-up: 10 seconds
- Measurement window: 60 seconds
- Concurrency: 1
- Attempts: 218
- Successes: 218
- Errors: 0
- Successful throughput: 3.617 requests/second
- p50: 260.98 ms
- p95: 320.23 ms
- p99: 411.04 ms
- Maximum: 1335.90 ms
- Error rate: 0%
- Mid-stage observation: 2026-09-09 02:20:23 UTC
- Mid-stage database connections: 14 total; Supavisor 1 idle and 0 active
- Supabase Observability snapshot: CPU 3%, memory 54%, peak connections 8/60, and disk I/O 1%
- Interpretation: Concurrency 1 was healthy. The authenticated database-backed read was slower than the health control, as expected, but remained well inside the five-second p99 stopping threshold with no errors.