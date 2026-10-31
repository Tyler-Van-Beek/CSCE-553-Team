from django.db import migrations

SEARCH_SQL = """
drop materialized view if exists search.event_search;


create materialized view search.event_search as 
select 
  e."EventID" as "Event ID", 
  e."Title" as "Title", 
  e."Description" as "Description", 
  e."Location" as "Location", 
  e."DateTime" as "Date/Time", 
  c."Name" as "Category",
  u.first_name as "Organizer First Name", 
  u.last_name as "Organizer Last Name", 
  setweight(to_tsvector('english', e."Title"), 'A') ||
  setweight(to_tsvector('english', coalesce(e."Description", '')), 'B') ||
  setweight(to_tsvector('english', e."Location"), 'C') ||
  setweight(to_tsvector('english', c."Name"), 'D') ||
  setweight(to_tsvector('english', coalesce(u.first_name, '') ||  ' ' || coalesce(u.last_name, '')), 'D') as fts
from events_event e
left join events_users u on u."UserID" = e."OrganizerID_id"
left join events_category c on c."CategoryID" = e."CategoryID_id";
"""

class Migration(migrations.Migration):
    dependencies = [("events", "0007_productsearch")]
    operations = [
        migrations.RunSQL(
            SEARCH_SQL,
            reverse_sql=
                "drop scheme search cascade;",
        )
    ]