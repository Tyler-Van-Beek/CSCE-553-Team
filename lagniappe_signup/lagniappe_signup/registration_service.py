from django.db import connections, transaction

from events.models import Event, Registration

from .shard_routing import shard_for_event


def register_on_event_shard(*, event_id: int, user_id: int) -> tuple[Registration, bool]:
    """Register an authenticated user and return the row and whether it was created."""
    alias = shard_for_event(event_id)

    with transaction.atomic(using=alias):
        if not Event.objects.using(alias).filter(pk=event_id).exists():
            raise Event.DoesNotExist
        with connections[alias].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.m6_user_reference ("UserID")
                VALUES (%s)
                ON CONFLICT ("UserID") DO NOTHING
                """,
                [user_id],
            )

        return Registration.objects.using(alias).get_or_create(
            EventID_id=event_id,
            UserID_id=user_id,
        )