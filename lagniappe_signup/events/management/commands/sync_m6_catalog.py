from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from lagniappe_signup.catalog_sync import sync_event_catalog


class Command(BaseCommand):
    help = "Sync event changes from both M6 shards and refresh the search view."

    def handle(self, *args, **options):
        aliases = ("shard_0", "shard_1")
        if any(alias not in connections.databases for alias in aliases):
            raise CommandError("Configure both M6 shard connections first.")

        for alias in aliases:
            changes_applied = sync_event_catalog(alias)
            self.stdout.write(f"{alias}: {changes_applied} catalog changes applied.")

        with connections["default"].cursor() as cursor:
            cursor.execute(
                "REFRESH MATERIALIZED VIEW CONCURRENTLY search.event_search"
            )

        self.stdout.write(self.style.SUCCESS("Search view refreshed."))