ALTER TABLE events_event
ADD CONSTRAINT events_belong_here
CHECK (
    shard_bucket("EventID")
    BETWEEN :min_bucket AND :max_bucket
);