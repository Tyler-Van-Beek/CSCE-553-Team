from django.core.exceptions import ImproperlyConfigured
from django.db import connections


def shard_for_event(event_id: int) -> str:
    """Return the database alias that owns this event."""
    with connections["shard_0"].cursor() as cursor:
        cursor.execute(
            """
            SELECT shard
            FROM m6_bucket_map
            WHERE bucket = shard_bucket(%s)
            """,
            [event_id],
        )
        row = cursor.fetchone()

    if row is None:
        raise ImproperlyConfigured(f"No shard mapping for event {event_id}.")

    return row[0]