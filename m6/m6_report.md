# Milestone 6: Sharding Lagniappe Sign-Up

## Objective and result

I partitioned event, registration, and feedback data across two PostgreSQL
shards using `EventID` as the shard key. I verified that Django routed
registration writes to both shards and that M5 search returned events from
both shards after catalog sync and refresh.

In a matched local benchmark, both setups committed the same 90,000
registration inserts with zero reported failures. The single database
processed 8,004 writes/sec. The two shards together processed approximately
7,175 writes/sec, 10.4% lower in this run. Both shards ran in Docker on the
same laptop and shared its CPU and storage. Performance on separate
database hosts remains unmeasured.

## Data model before and after sharding

| Data | Before sharding | After sharding in the local setup |
|---|---|---|
| Events | All events in one PostgreSQL database | One authoritative row on the shard that owns the event |
| Registrations and feedback | Stored in the same database as all events | Stored with their event, using `EventID` to route reads and writes |
| Categories | One lookup table | Copied to both shards with the same category IDs |
| Users and authentication | Full user accounts and authentication in one database | Full accounts and authentication stay in the default database. Each shard stores user ID references for its foreign keys. |
| Event catalog and M5 search | Search view built from the event table | The default database holds a catalog of events from both shards. The `sync_m6_catalog` command applies queued changes and refreshes the search view. |

### Why I chose EventID

An event’s ID stays the same when its details change. Registration,
cancellation, feedback, and event edits already have an event ID when
they run. For a new event, Django reserves an integer ID from a shared
sequence before choosing a shard.

Django hashes the ID into one of 64 buckets. Shard 0 owns buckets 0–31,
and shard 1 owns buckets 32–63. A database constraint rejects events
assigned to the wrong shard. Registrations and feedback reference their
event locally, so a per-event attendee list can query one database.

The trade-off is that one popular event still sends all its writes to
one shard. A user’s registration history can also span both shards,
so Django combines those results before paginating.

## Before sharding: Write bottleneck

I used `pgbench` to insert registrations directly into one PostgreSQL 16
database running in Docker. Both runs used four worker threads and
90,000 unique user–event pairs. Each run used a fresh set of pairs, so
the registration table grew between runs.

| Concurrent clients | Committed inserts | Writes/sec | Avg. transaction latency |
|---:|---:|---:|---:|
| 75 | 90,000 | 7,473.03 | 10.036 ms |
| 90 | 90,000 | 6,692.56 | 13.448 ms |

At 90 clients, throughput fell by 10.4% and average latency rose by 34.0%.
In one snapshot, 89 sessions were waiting on `WALWrite` and one was
waiting on `WALSync`. These samples point to contention in PostgreSQL’s
write-ahead log under concurrent registration writes.

## Matched benchmark: One database versus two shards

For the comparison, I used the same 90,000 user–event pairs in both
setups. The single database ran with 90 clients and four worker threads.
The two shards ran concurrently, each with 45 clients and two worker
threads. I verified that each shard committed 45,000 matching inserts.

| Setup | Committed inserts | Failed transactions | Writes/sec | Avg. transaction latency |
|---|---:|---:|---:|---:|
| One database | 90,000 | 0 | 8,004.40 | 11.244 ms |
| Two shards | 90,000 | 0 | 7,175.45 | 12.543 ms |

The two-shard throughput is the sum of the two `pgbench` rates.
The latency is weighted by the number of transactions on each shard.
In this run, throughput was 10.4% lower and average latency was 11.6%
higher with two shards. Both containers shared the laptop’s CPU and
storage. These results measure direct PostgreSQL performance in Docker.
Performance through Django and on separate database hosts remains
unmeasured for the matched comparison.

## Django routing and M5 search verification

| Test | Observed result |
|---|---|
| Create registrations through the API | Registration `545570` for event `6` existed only on shard 0. Registration `545567` for event `4` existed only on shard 1. |
| Reject a duplicate and cancel a registration | A repeat signup returned HTTP 409. Cancellation returned HTTP 204, and SQL confirmed the row was removed from shard 1. |
| Read registrations | Both per-event pagination endpoints returned the expected rows. My Registrations returned rows from both shards for user `2000`. |
| Use the browser | Browser signup and cancellation for event `4` were verified on shard 1. Feedback for event `6` was saved on shard 0 and appeared in the feedback list. |
| Search across shards | After running `sync_m6_catalog`, one `/api/search?q=M6` request returned event `1001` from shard 1 and event `1002` with its edited title from shard 0. |
| Remove a searchable event | Event `1003` appeared in the search view before deletion. After deletion, catalog sync, and refresh, SQL confirmed it was absent from both the catalog and the search view. |

These checks ran against the local Docker databases. Catalog sync and
search refresh were triggered manually during testing.

## Worksheet and limitations

[Sharding worksheet](sharding_worksheet.md)

The worksheet records the five write actions, their owners, and the
choice of EventID as the shard key. Busy-hour frequencies remain
unmeasured because the tests used synthetic traffic.

The matched benchmark ran once per setup. Both used the same 90,000
user–event pairs, but the single database ran first and the two shards
shared one laptop’s CPU and storage. The results describe direct
PostgreSQL performance in that setup. End-to-end Django write
performance and throughput on separate database hosts remain unmeasured.

I ran catalog sync and search refresh manually during local testing.
The Azure + Supabase sharded deployment is still pending. The existing
M5 deployment continued using its original database.