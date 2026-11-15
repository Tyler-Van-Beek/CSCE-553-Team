# M6 Sharding Worksheet: Lagniappe Sign-Up

## Step 1: List the busiest writes

These five write actions were verified in the Django code. Their busy-hour
frequencies and ranking are still unknown.

| User action | SQL write | Table | Busy-hour frequency |
|---|---|---|---|
| Register for an event | INSERT | `events_registration` | Not measured |
| Cancel a registration | DELETE | `events_registration` | Not measured |
| Create an event | INSERT | `events_event` | Not measured |
| Update an event | UPDATE | `events_event` | Not measured |
| Submit event feedback | INSERT | `events_feedback` | Not measured |

## Step 2: Identify the write owner and choose a shard key

| Action | Row changed today | Proposed owner | Owner ID column |
|---|---|---|---|
| Register for an event | New registration row | Event | `events_registration.EventID_id` |
| Cancel a registration | Existing registration row | Event | `events_registration.EventID_id` |
| Create an event | New event row | Event | `events_event.EventID` |
| Update an event | Existing event row | Event | `events_event.EventID` |
| Submit event feedback | New feedback row | Event | `events_feedback.EventID_id` |

**Proposed shard key: `EventID`.** Keep each event and its authoritative
registrations and feedback on the same shard.

- **Available before the write:** Existing-event actions already have the
  event ID. New events need a globally unique ID before shard routing.
- **Stable:** `EventID` stays the same when event details change.
- **Many values:** Hash event IDs into 64 fixed buckets. Shard 0 gets
  buckets 0–31, and shard 1 gets buckets 32–63.

Registration and cancellation currently change only the registration row.
If capacity is added, the seat update and registration write must succeed
or fail together on the event's shard.

The per-event registration list can keep its keyset cursor on one shard.
A user's registration history may span shards. M5 search needs an event
catalog that covers all events.

## Baseline write evidence

I used pgbench to test registration inserts directly against one unsharded
PostgreSQL 16 database in local Docker. Both runs used four pgbench worker
threads and 90,000 distinct user–event pairs.

| Concurrent clients | Successful inserts | Failed transactions | Writes/sec | Avg. transaction latency |
|---:|---:|---:|---:|---:|
| 75 | 90,000 | 0 | 7,473.03 | 10.036 ms |
| 90 | 90,000 | 0 | 6,692.56 | 13.448 ms |

From 75 to 90 clients, throughput fell by 10.4% and average latency rose
by 34.0%. In one 90-client snapshot, 89 sessions were waiting on `WALWrite`
and one was waiting on `WALSync`. The samples point to contention in
PostgreSQL's write-ahead log during concurrent registration inserts.

The runs used successive batches of fresh pairs, so the registration table
grew between runs. These results describe a synthetic local workload.
Busy-hour frequencies in Step 1 remain marked "Not measured."

## Method Step 2: Table placement

Hash each EventID into one of 64 fixed buckets. Shard 0 owns buckets 0–31,
and shard 1 owns buckets 32–63.

| Data | Location in the local setup | Routing |
|---|---|---|
| Events | One authoritative copy on the event's shard | Route by `EventID` |
| Registrations and feedback | Same shard as their event | Route by `EventID` from the row or request |
| Categories | Copied to both shards with matching IDs | Look up categories on the event's shard |
| Users, auth tokens, and sessions | Django's `default` PostgreSQL database (`lagniappe_m6`) | Authenticate before routing event writes |
| User references needed by shard foreign keys | User ID references on each shard | Use the same user IDs as the `default` database |
| Event catalog for list and search | Django's `default` PostgreSQL database (`lagniappe_m6`), populated from both shards | Search the full catalog |
| Bucket map | Shard 0 (`lagniappe_m6_shard0`) | Map each bucket to its owning shard |

The per-event registration list and its keyset cursor query one shard.
For the initial two-shard design, "My registrations" queries both shards
by UserID and merges the results before pagination.

Before implementation, decide how to assign globally unique event IDs before
routing and how to keep the catalog and user references in sync.


### Event ID allocation

Keep the existing integer EventID values. For each new event, Django
reserves an ID from a single sequence in the central M6 database on
shard 0. Initialize that sequence above the highest existing EventID
across both shards. Django hashes the reserved ID to choose the shard,
then inserts the event there with that explicit ID.

This gives both shards a shared source of unique event IDs while keeping
the current integer URLs. Registration and cancellation use the event's
existing ID and require no sequence allocation.

### Event catalog and M5 search

When Django creates, edits, or deletes an event, it saves the change
and queues a catalog update in the same transaction on the event's shard.

The `sync_m6_catalog` command applies queued updates from both shards
to Django's `default` database (`lagniappe_m6`), then refreshes the M5
search view. The event list and search use this shared catalog.

I ran the command manually during local testing. A five-minute schedule
for the M6 deployment is still pending.

A background worker copies the event's ID, title, description, location,
date, status, and category ID into the central M6 catalog on shard 0.
It inserts or updates the catalog row by EventID. If the copy fails,
the worker retries it. Updates for the same event are applied in order
so an older edit cannot overwrite a newer one.

The M6 event list and search read from the central catalog, which
contains events from both shards. The M6 search view keeps M5's
full-text ranking and five-minute refresh schedule. A new event or
edit appears in search after the catalog copy and the next refresh.

### User references on each shard

Keep user accounts and authentication in the central M6 database.
Each event shard stores a user reference keyed by the same UserID.
The reference stores only the ID.

Before creating an event, registration, or feedback row, Django
verifies the user centrally and ensures the reference exists on the
target shard. The reference and the new row are saved in one local
transaction. The event's organizer and the registration and feedback
user foreign keys point to these local references.
## Matched before-and-after write benchmark

Both setups inserted the same 90,000 unique user–event pairs using
pgbench, with 90 clients and four worker threads in total. The two
shards ran concurrently, with 45 clients and two threads per shard.

| Setup | Committed inserts | Failed transactions | Writes/sec | Avg. transaction latency |
|---|---:|---:|---:|---:|
| One PostgreSQL database | 90,000 | 0 | 8,004.40 | 11.244 ms |
| Two PostgreSQL shards | 90,000 | 0 | 7,175.45 | 12.543 ms |

I verified 45,000 matching rows on each shard. The combined throughput
is the sum of the two pgbench rates, excluding initial connection time.
Average latency is weighted by the number of transactions on each shard.

In this local run, sharding reduced throughput by 10.4% and increased
average latency by 11.6%. Both shards shared the same laptop's CPU and
storage. This was one direct PostgreSQL comparison. Django request
latency and performance on separate database hosts are still unmeasured.