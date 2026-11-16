BEGIN;

-- M5 PostgreSQL full-text search setup
-- Run against the existing Lagniappe PostgreSQL database.
-- The materialized view and search function are also used by Django.

CREATE SCHEMA IF NOT EXISTS m6_search;

CREATE MATERIALIZED VIEW IF NOT EXISTS m6_search.event_search AS
SELECT
    e."EventID",
    e."Title",
    e."Description",
    e."Location",
    e."DateTime",
    e."EventStatus",
    c."Name" AS category,
    setweight(
        to_tsvector('english', COALESCE(e."Title", '')), 'A'
    ) ||
    setweight(
        to_tsvector('english', COALESCE(c."Name", '')), 'B'
    ) ||
    setweight(
        to_tsvector('english', COALESCE(e."Location", '')), 'B'
    ) ||
    setweight(
        to_tsvector('english', COALESCE(e."Description", '')), 'C'
    ) AS fts
FROM m6_catalog.events_event e
LEFT JOIN m6_catalog.events_category c
    ON e."CategoryID_id" = c."CategoryID"
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS event_search_id_idx
ON m6_search.event_search ("EventID");

CREATE INDEX IF NOT EXISTS event_search_fts_idx
ON m6_search.event_search USING GIN (fts);

CREATE OR REPLACE FUNCTION m6_search.search_events(
    q TEXT,
    cat TEXT DEFAULT NULL,
    active_only BOOLEAN DEFAULT TRUE,
    lim INTEGER DEFAULT 20,
    off INTEGER DEFAULT 0
)
RETURNS TABLE (
    event_id INTEGER,
    title VARCHAR,
    category VARCHAR,
    location VARCHAR,
    event_datetime TIMESTAMPTZ,
    rank REAL
)
LANGUAGE SQL STABLE AS $$
    SELECT
        s."EventID",
        s."Title",
        s.category::VARCHAR,
        s."Location",
        s."DateTime",
        ts_rank(
            s.fts,
            websearch_to_tsquery('english', q)
        ) AS rank
    FROM m6_search.event_search s
    WHERE s.fts @@ websearch_to_tsquery('english', q)
      AND (cat IS NULL OR s.category = cat)
      AND (NOT active_only OR s."EventStatus" = TRUE)
    ORDER BY rank DESC, s."EventID"
    LIMIT LEAST(GREATEST(lim, 1), 50)
    OFFSET GREATEST(off, 0);
$$;

COMMIT;
