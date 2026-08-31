from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Category, Event, Users


DEMO_PASSWORD = "ClassDemo123!"

DEMO_USERS = [
    {
        "email": "alex.demo@example.com",
        "first_name": "Alex",
        "last_name": "Demo",
    },
    {
        "email": "blair.demo@example.com",
        "first_name": "Blair",
        "last_name": "Demo",
    },
    {
        "email": "casey.demo@example.com",
        "first_name": "Casey",
        "last_name": "Demo",
    },
]

DEMO_EVENTS = [
    {
        "title": "Community Meetup",
        "description": "A friendly local meetup for neighbors.",
        "location": "Community Center",
        "category": "Community",
    },
    {
        "title": "River Walk",
        "description": "A casual group walk along the river.",
        "location": "River Trail",
        "category": "Outdoor",
    },
    {
        "title": "Coding Workshop",
        "description": "A beginner-friendly software workshop.",
        "location": "Public Library",
        "category": "Education",
    },
]


class Command(BaseCommand):
    help = "Create fake CSCE 553 demo users, categories, and events."

    def handle(self, *args, **options):
        users = []

        for user_data in DEMO_USERS:
            email = user_data["email"]

            user, created = Users.objects.get_or_create(
                username=email,
                defaults={
                    "email": email,
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                },
            )

            user.email = email
            user.first_name = user_data["first_name"]
            user.last_name = user_data["last_name"]

            update_fields = [
                "email",
                "first_name",
                "last_name",
            ]

            if created:
                user.set_password(DEMO_PASSWORD)
                update_fields.append("password")

            user.save(update_fields=update_fields)
            users.append(user)

            action = "Created" if created else "Reused"
            self.stdout.write(f"{action} demo user {email}")

        for index, event_data in enumerate(DEMO_EVENTS):
            category, _ = Category.objects.get_or_create(
                Name=event_data["category"]
            )

            event, created = Event.objects.get_or_create(
                OrganizerID=users[index],
                Title=event_data["title"],
                defaults={
                    "CategoryID": category,
                    "Description": event_data["description"],
                    "Location": event_data["location"],
                    "DateTime": timezone.now()
                    + timedelta(days=index + 1),
                    "EventStatus": True,
                },
            )

            if not created:
                event.CategoryID = category
                event.Description = event_data["description"]
                event.Location = event_data["location"]
                event.EventStatus = True
                event.save(
                    update_fields=[
                        "CategoryID",
                        "Description",
                        "Location",
                        "EventStatus",
                    ]
                )

            action = "Created" if created else "Reused"
            self.stdout.write(
                f"{action} demo event {event.Title}"
            )

        self.stdout.write(
            self.style.SUCCESS("Demo data is ready.")
        )