from django.db import connections, transaction

from events.models import Event

from .shard_routing import shard_for_event


def create_event_on_shard(*, organizer_id, category_id, **event_fields):
    with connections["shard_0"].cursor() as cursor:
        cursor.execute("SELECT nextval('m6_event_id_seq')")
        event_id = cursor.fetchone()[0]

    alias = shard_for_event(event_id)

    with transaction.atomic(using=alias):
        with connections[alias].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO m6_user_reference ("UserID")
                VALUES (%s)
                ON CONFLICT ("UserID") DO NOTHING
                """,
                [organizer_id],
            )

        event = Event.objects.using(alias).create(
            EventID=event_id,
            OrganizerID_id=organizer_id,
            CategoryID_id=category_id,
            **event_fields,
        )

        with connections[alias].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO m6_event_catalog_outbox (event_id, event_data)
                SELECT e."EventID", to_jsonb(e)
                FROM events_event AS e
                WHERE e."EventID" = %s
                """,
                [event_id],
            )

    return event

def update_event_on_shard(*, event, changes):
    alias = event._state.db
    fields = dict(changes)
    if "CategoryID" in fields:
        fields["CategoryID_id"] = fields.pop("CategoryID").pk

    if not fields:
        return event

    with transaction.atomic(using=alias):
        events = Event.objects.using(alias).filter(pk=event.pk)
        events.update(**fields)
        updated_event = events.get()

        with connections[alias].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO m6_event_catalog_outbox (event_id, event_data)
                SELECT e."EventID", to_jsonb(e)
                FROM events_event AS e
                WHERE e."EventID" = %s
                """,
                [event.pk],
            )

    return updated_event

def delete_event_on_shard(*, event):
    alias = event._state.db
    event_id = event.pk

    with transaction.atomic(using=alias):
        event.delete(using=alias)

        with connections[alias].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO m6_event_catalog_outbox (event_id, event_data)
                VALUES (%s, NULL)
                """,
                [event_id],
            )