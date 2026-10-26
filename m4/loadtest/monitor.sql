-- Run these in the Supabase SQL Editor while a load test is running.

-- 1. Which queries take the most database time?
--    (pg_stat_statements is usually enabled on Supabase; if not, enable it
--    under Database > Extensions.)
SELECT calls,
       round(mean_exec_time::numeric, 2)  AS mean_ms,
       round(total_exec_time::numeric)    AS total_ms,
       rows,
       left(query, 100)                   AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- 2. How many connections are open, and what are they doing?
--    Many 'active' = the database is busy. Close to the limit = pool exhaustion.
SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;

SHOW max_connections;

-- 3. Start fresh before each test run, so step 1 shows only that run.
-- SELECT pg_stat_statements_reset();
