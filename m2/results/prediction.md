# M2 Pre-Measurement Workload and Capacity Model

Prediction recorded: 2026-09-07 23:41:45 -05:00

This model was written before running any 60-second M2 performance tests.

## System under test

Lagniappe Sign-Up is an event-management application. The current M1 architecture consists of one Django API process hosted on Render and one PostgreSQL database hosted on Supabase.

Architecture:

Load generator -> Django API -> PostgreSQL

## Workload assumptions

- Active users during the peak hour: 10% of registered users
- Actions per active user per hour: 6
- Workload mix: 80% reads and 20% writes
- Modeled read response size: 20,000 bytes
- Modeled write request/response size: 1,000 bytes
- Weighted bytes per operation: (0.80 x 20,000) + (0.20 x 1,000) = 16,200 bytes
- Stored bytes per write: 1,000 bytes
- Copies in the current M1 architecture: 1
- Planning mean latency before measurement: 0.25 seconds
- Storage calculations use decimal MB and GB.
- Indexes and backups are not included in the numerical storage estimate. In a production system, both would increase required storage.
- The modeled response size will be compared with the actual `GET /api/events` payload measured using curl before the load sweep.

## Formulas

Peak RPS = (active users x actions per active user per hour) / 3600

Write RPS = Peak RPS x 0.20

Storage per day = Write RPS x 86,400 x 1,000 bytes x 1 copy

Bandwidth = Peak RPS x 16,200 bytes x 1 copy

Estimated in-flight requests = Peak RPS x 0.25 seconds

## Capacity worksheet

| Registered users | Active users (10%) | Peak RPS | Write RPS | Storage/day | Bandwidth | Estimated in-flight |
|---:|---:|---:|---:|---:|---:|---:|
| 10,000 | 1,000 | 1.67 | 0.33 | 28.8 MB/day | 27 KB/s | 0.42 |
| 1,000,000 | 100,000 | 166.67 | 33.33 | 2.88 GB/day | 2.70 MB/s | 41.67 |
| 100,000,000 | 10,000,000 | 16,666.67 | 3,333.33 | 288 GB/day | 270 MB/s | 4,166.67 |

## Predicted first observable limit

The predicted first observable limit is saturation of the single Render API process CPU or its request queue, causing throughput to flatten and p99 latency to increase before PostgreSQL reaches its connection limit.

## Prediction justification

The hosted system uses one small Render web-service process, while Django is configured to reuse PostgreSQL connections with `conn_max_age=600`. Therefore, the API compute or request-processing capacity is expected to become constrained before the database exhausts its available connections. This prediction will be evaluated using latency, throughput, error rate, Render CPU and memory, and PostgreSQL connection measurements.

## Measurements to revise later

After the experiments:

- Replace or compare the modeled payload with the measured event-list response size.
- Recalculate the 10K row using measured healthy throughput and latency.
- Apply Little's Law to one healthy measured stage.
- Explain the architecture changes that would be required for 1M and 100M registered users without implementing those changes during M2.