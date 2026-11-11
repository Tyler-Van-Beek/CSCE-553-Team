# Feedback — Lagniappe Sign-Up

**Relative standing in this class: B.** Read from the code on 11 November 2026.

This letter is search and sharding. Those are the two pieces that set the standing. Other notes are at the end and are separate from it.

There is a search page and a search API, with facets and a page size. There is no sharding. The search does not rank the full-text column it stores. That combination is the B.

## Search

The materialized view `search.event_search` builds a weighted `fts` value: title, description, location, category, organizer name. That is the right document for event search.

The page and `/api/search` do not query it. The page builds a `tsquery` string and a `SearchQuery` and never applies either one. Both paths score trigram similarity plus an OpenAI embedding, and they do not use the same cutoffs (`0.15` / `0.30` on the page, `0.05` / `0.70` on the API). The embedding call also means search fails closed or open depending on which path catches the error: the page returns no rows, the API falls back to trigram.

The view SQL in migrations `0008` and `0010` names columns one way (`"Title"`, `"Event ID"`). `EventSearch` expects another (`title`, `id`). One relation, one set of names.

What to change: one search function for the page and the API. Rank with `fts`. Refresh the materialized view when an event, category, or organizer name changes, or a new event never enters search. Keep the embedding as a second score you can turn off, not as the only rank. Until `fts` is the predicate, the GIN-shaped document you built is not the index the query uses.

Keyset pagination on registrations is separate from search and is in good shape. It is not a substitute for sharding, and it is not the search rank.

## Sharding

Events, registrations, and users live in one database. Nothing routes a request by a shard key.

The placement that fits this app: a user's registrations live with the user, and the event list is a catalog you either copy to every shard or keep on one catalog database and say so. Search runs against that catalog, not against whichever shard the last request happened to open. Registration for one event, the list you already page with a cursor, is the hot read that has to declare its shard: all registrations for an event on the event's shard, so the cursor does not have to merge two sequences.

This repository does not do that. The standing stays a B until the serving path has a shard, even after search ranks `fts`.

## Software engineering notes

These do not change the standing.

- The HTML views write events, registrations, and feedback on their own. The registration form posts a chosen user id and saves that row. The API binds the registration to the logged-in user. The page should call the same operations as the API, and the registered user should be the logged-in user.
- `list_reg`, `list_feedback`, and `list_users` set `paginate = 20`. Django reads `paginate_by`, so those pages return the full table. `list_event` pages at 30 and also builds `EventSerializer` over the unpaged queryset, then discards it.
- `EventStatus` is a boolean, `DateTime` can be null, and registration does not stop when the room is full. A finished sign-up has a capacity and fails the insert that would pass it.
- Event list and search require a token. A public board can leave create, register, and feedback authenticated and let anonymous visitors search. If the board is private, the token on the read is the right rule. Pick one.
