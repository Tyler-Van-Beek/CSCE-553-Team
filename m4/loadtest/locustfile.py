"""
Closed-loop load test with Locust.

Each simulated user sends a request, waits for the response, pauses
("think time"), and repeats. Good for realistic user journeys; remember that
when the server slows down, a closed loop sends fewer requests (lecture 2).

Edit ENDPOINTS to match your API. {placeholders} are filled with ids from
loadtest_ids.json (written by the seed scripts), so popular rows are
requested more often, as in real traffic.

Run with the web UI (open http://localhost:8089):
  locust -f locustfile.py --host http://YOUR-APP:8000

Run headless, ramping to 500 users, saving results to CSV:
  locust -f locustfile.py --host http://YOUR-APP:8000 \
         --headless -u 500 -r 5 -t 10m --csv results
"""
import json
import os
import random

from locust import HttpUser, between, task

# =============================== CONFIG ===============================

# (weight, name shown in the results, path). Weights set the traffic mix.
ENDPOINTS = [
    (5, "events page 1", "/api/events"),
    (2, "events deep page", "/api/events?page={deep_page}"),
    #(4, "event registrations offset", "/api/events/{event_id}/registrations"),
    #(4, "event registrations keyset", "/api/events/{event_id}/registrations-keyset"),
    (4, "hot event offset deep", "/api/events/2464/registrations?page=251"),
    (4, "hot event keyset deep", "/api/events/2464/registrations-keyset?after=133019"),
]
# Extra placeholder values that do not come from the seed data.
EXTRA_VALUES = {"deep_page": list(range(50, 180))}

# Think time between a user's requests, in seconds.
THINK_TIME = between(1, 3)

# If your API needs a token, set API_TOKEN in the environment.
TOKEN = os.environ.get("API_TOKEN")

# ============================ END CONFIG ==============================

with open(os.environ.get("IDS_FILE", "loadtest_ids.json")) as f:
    VALUES = {**json.load(f), **EXTRA_VALUES}

WEIGHTS = [w for w, _, _ in ENDPOINTS]


def fill(template):
    """Replace each {name} with a random value from VALUES[name]."""
    keys = [part.split("}")[0] for part in template.split("{")[1:]]
    return template.format(**{k: random.choice(VALUES[k]) for k in keys})


class AppUser(HttpUser):
    wait_time = THINK_TIME

    def on_start(self):
        if TOKEN:
            self.client.headers["Authorization"] = f"Token {TOKEN}"
        # Or log in with a session cookie, for example:
        # self.client.post("/login", json={"email": "user1@example.com", "password": "..."})

    @task
    def browse(self):
        _, name, template = random.choices(ENDPOINTS, weights=WEIGHTS)[0]
        # name= groups all requests to one endpoint in the results,
        # instead of one row per distinct id.
        self.client.get(fill(template), name=name)
