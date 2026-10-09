import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import (
    Users,
    Category,
    Event,
    Registration,
    Feedback,
)


RANDOM_SEED = 533
TEST_PASSWORD = "ClassDemo123!"

CATEGORY_NAMES = [
    "Community",
    "Education",
    "Technology",
    "Outdoor",
    "Career",
    "Sports",
    "Health",
    "Arts",
    "Music",
    "Food",
]


class Command(BaseCommand):
    help = "Create realistic, skewed M4 database-scaling test data."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=2000)
        parser.add_argument("--events", type=int, default=1000)
        parser.add_argument("--registrations", type=int, default=20000)
        parser.add_argument("--feedback", type=int, default=5000)

    def handle(self, *args, **options):
        random.seed(RANDOM_SEED)

        user_count = options["users"]
        event_count = options["events"]
        registration_count = options["registrations"]
        feedback_count = options["feedback"]

        self.stdout.write("Starting M4 realistic data generation...")

        # -------------------------------------------------
        # Categories
        # -------------------------------------------------
        categories = []

        for name in CATEGORY_NAMES:
            category, _ = Category.objects.get_or_create(Name=name)
            categories.append(category)

        self.stdout.write(
            f"Categories ready: {len(categories)}"
        )

        # -------------------------------------------------
        # Users
        # -------------------------------------------------
        existing_users = Users.objects.filter(
            username__startswith="m4_user_"
        )

        existing_user_count = existing_users.count()

        if existing_user_count < user_count:
            shared_password_hash = make_password(TEST_PASSWORD)

            users_to_create = []

            for i in range(existing_user_count, user_count):
                email = f"m4_user_{i}@example.com"

                users_to_create.append(
                    Users(
                        username=email,
                        email=email,
                        first_name=f"M4User{i}",
                        last_name="Test",
                        password=shared_password_hash,
                    )
                )

            Users.objects.bulk_create(
                users_to_create,
                batch_size=1000,
            )

        users = list(
            Users.objects.filter(
                username__startswith="m4_user_"
            )
            .order_by("UserID")[:user_count]
        )

        self.stdout.write(
            f"Users ready: {len(users)}"
        )

        # -------------------------------------------------
        # Events
        # -------------------------------------------------
        existing_event_count = Event.objects.filter(
            Title__startswith="M4 Event"
        ).count()

        if existing_event_count < event_count:
            events_to_create = []

            now = timezone.now()

            for i in range(existing_event_count, event_count):

                # Skew organizers so some users create more events.
                organizer_index = min(
                    int(random.paretovariate(1.5)),
                    len(users) - 1,
                )

                organizer = users[organizer_index]
                category = random.choice(categories)

                events_to_create.append(
                    Event(
                        OrganizerID=organizer,
                        CategoryID=category,
                        Title=f"M4 Event {i}",
                        Description=f"Generated M4 event {i}",
                        Location=f"Location {i % 50}",
                        DateTime=now
                        + timedelta(
                            days=random.randint(-180, 180)
                        ),
                        EventStatus=True,
                    )
                )

            Event.objects.bulk_create(
                events_to_create,
                batch_size=1000,
            )

        events = list(
            Event.objects.filter(
                Title__startswith="M4 Event"
            )
            .order_by("EventID")[:event_count]
        )

        self.stdout.write(
            f"Events ready: {len(events)}"
        )

        # -------------------------------------------------
        # Registrations
        # -------------------------------------------------

        # Lower-ranked events receive more registrations.
        # This creates a skewed / long-tail distribution.
        popularity_weights = [
            1 / ((i + 1) ** 1.1)
            for i in range(len(events))
        ]

        existing_pairs = set(
            Registration.objects.filter(
                EventID__in=events,
                UserID__in=users,
            ).values_list(
                "UserID_id",
                "EventID_id",
            )
        )

        registrations_to_create = []

        attempts = 0
        max_attempts = registration_count * 20

        while (
            len(existing_pairs) < registration_count
            and attempts < max_attempts
        ):
            attempts += 1

            user = random.choice(users)

            event = random.choices(
                events,
                weights=popularity_weights,
                k=1,
            )[0]

            pair = (
                user.UserID,
                event.EventID,
            )

            if pair in existing_pairs:
                continue

            existing_pairs.add(pair)

            registrations_to_create.append(
                Registration(
                    UserID=user,
                    EventID=event,
                    RegistrationStatus=True,
                )
            )

            if len(registrations_to_create) >= 1000:
                Registration.objects.bulk_create(
                    registrations_to_create,
                    batch_size=1000,
                    ignore_conflicts=True,
                )

                registrations_to_create = []

        if registrations_to_create:
            Registration.objects.bulk_create(
                registrations_to_create,
                batch_size=1000,
                ignore_conflicts=True,
            )

        registration_pairs = list(
            Registration.objects.filter(
                EventID__in=events,
                UserID__in=users,
            ).values_list(
                "UserID_id",
                "EventID_id",
            )
        )

        self.stdout.write(
            f"Registrations ready: {len(registration_pairs)}"
        )

        # -------------------------------------------------
        # Feedback
        # -------------------------------------------------

        existing_feedback_pairs = set(
            Feedback.objects.filter(
                EventID__in=events,
                UserID__in=users,
            ).values_list(
                "UserID_id",
                "EventID_id",
            )
        )

        current_feedback_count = len(existing_feedback_pairs)

        needed_feedback = max(
            0,
            feedback_count - current_feedback_count,
        )

        self.stdout.write(
            f"Existing M4 feedback: {current_feedback_count}"
        )

        if needed_feedback > 0:

            available_pairs = [
                pair
                for pair in registration_pairs
                if pair not in existing_feedback_pairs
            ]

            random.shuffle(available_pairs)

            pairs_to_create = available_pairs[
                :needed_feedback
            ]

            feedback_to_create = []

            for user_id, event_id in pairs_to_create:
                feedback_to_create.append(
                    Feedback(
                        UserID_id=user_id,
                        EventID_id=event_id,
                        Rating=random.randint(1, 5),
                        Comments=(
                            f"Generated M4 feedback for "
                            f"event {event_id} by user {user_id}"
                        ),
                    )
                )

            Feedback.objects.bulk_create(
                feedback_to_create,
                batch_size=1000,
                ignore_conflicts=True,
            )

        final_feedback_count = Feedback.objects.filter(
            EventID__in=events,
            UserID__in=users,
        ).count()

        self.stdout.write(
            f"Feedback ready: {final_feedback_count}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "M4 realistic dataset generation complete."
            )
        )