ALTER TABLE public.events_event
ADD CONSTRAINT events_belong_here
CHECK (
    public.shard_bucket("EventID")
    BETWEEN :min_bucket AND :max_bucket
);