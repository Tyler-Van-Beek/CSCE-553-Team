CREATE TABLE IF NOT EXISTS public.m6_event_catalog_outbox (
    change_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id integer NOT NULL,
    event_data jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);