from django.db import connections, transaction
from events.models import Event

def sync_event_catalog(alias):
    """Copy up to 100 pending event creates and edits from one shard."""
    with transaction.atomic(using=alias):
        with connections[alias].cursor() as source:
            # Let only one sync process drain this shard at a time.
            source.execute("SELECT pg_advisory_xact_lock(553, 6)")
            source.execute(
                """
                SELECT change_id, event_id,event_data::text
                FROM m6_event_catalog_outbox
                ORDER BY change_id
                LIMIT 100
                """
            )
            changes = source.fetchall()

            with transaction.atomic(using="default"):
                with connections["default"].cursor() as catalog:
                    for _, event_id, event_data in changes:
                        if event_data is None:
                            # Handle deletion
                            Event.objects.using("default").filter(pk=event_id).delete()
                            continue

                        catalog.execute(
                            """
                            INSERT INTO events_event (
                                "EventID", "Title", "Description", "Location",
                                "DateTime", "EventStatus", "CategoryID_id", "OrganizerID_id"
                            )
                            SELECT "EventID", "Title", "Description", "Location",
                                   "DateTime", "EventStatus", "CategoryID_id", "OrganizerID_id"
                            FROM json_populate_record(NULL::events_event, %s::json)
                            ON CONFLICT ("EventID") DO UPDATE SET
                                "Title" = EXCLUDED."Title",
                                "Description" = EXCLUDED."Description",
                                "Location" = EXCLUDED."Location",
                                "DateTime" = EXCLUDED."DateTime",
                                "EventStatus" = EXCLUDED."EventStatus",
                                "CategoryID_id" = EXCLUDED."CategoryID_id",
                                "OrganizerID_id" = EXCLUDED."OrganizerID_id"
                            """,
                            [event_data],
                        )

            # Acknowledge changes only after the catalog transaction commits.
            if changes:
                source.execute(
                    """
                    DELETE FROM m6_event_catalog_outbox
                    WHERE change_id = ANY(%s)
                    """,
                    [[change_id for change_id, _, _ in changes]],
                )

    return len(changes)