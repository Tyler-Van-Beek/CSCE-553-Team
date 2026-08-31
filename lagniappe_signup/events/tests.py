from django.test import TestCase

# Create your tests here.

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category,Users, Event
from rest_framework.authtoken.models import Token
from io import StringIO

from django.core.management import call_command

class HealthEndpointTests(SimpleTestCase):
    def test_health_returns_ok(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

class SeedDemoDataTests(TestCase):
    def test_seed_command_is_idempotent(self):
        first_output = StringIO()
        call_command(
            "seed_demo_data",
            stdout=first_output,
        )

        demo_users = Users.objects.filter(
            email__endswith=".demo@example.com"
        )
        demo_events = Event.objects.filter(
            OrganizerID__in=demo_users
        )

        self.assertEqual(demo_users.count(), 3)
        self.assertEqual(demo_events.count(), 3)
        self.assertEqual(Category.objects.count(), 3)
        self.assertTrue(
            all(
                user.check_password("ClassDemo123!")
                for user in demo_users
            )
        )

        original_user_ids = set(
            demo_users.values_list("UserID", flat=True)
        )
        original_event_ids = set(
            demo_events.values_list("EventID", flat=True)
        )

        second_output = StringIO()
        call_command(
            "seed_demo_data",
            stdout=second_output,
        )

        demo_users = Users.objects.filter(
            email__endswith=".demo@example.com"
        )
        demo_events = Event.objects.filter(
            OrganizerID__in=demo_users
        )

        self.assertEqual(demo_users.count(), 3)
        self.assertEqual(demo_events.count(), 3)
        self.assertEqual(
            set(demo_users.values_list("UserID", flat=True)),
            original_user_ids,
        )
        self.assertEqual(
            set(demo_events.values_list("EventID", flat=True)),
            original_event_ids,
        )
        self.assertIn(
            "Demo data is ready.",
            second_output.getvalue(),
        )

class AuthenticationApiTests(APITestCase):
    def test_registration_login_authenticated_request_and_logout(self):
        credentials = {
            "email": "automated_api_test@example.com",
            "password": "TemporaryTest123!",
            "first_name": "Automated",
            "last_name": "Tester",
        }

        registration_response = self.client.post(
            reverse("api-register"),
            credentials,
            format="json",
        )

        self.assertEqual(
            registration_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertNotIn("password", registration_response.data)

        user = Users.objects.get(email=credentials["email"])
        self.assertTrue(user.check_password(credentials["password"]))
        self.assertEqual(user.first_name, "Automated")
        self.assertEqual(user.last_name, "Tester")
        self.assertEqual(
            registration_response.data["first_name"],
            "Automated",
        )
        self.assertEqual(
            registration_response.data["last_name"],
            "Tester",
        )

        login_response = self.client.post(
            reverse("api-login"),
            credentials,
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("token", login_response.data)

        token = login_response.data["token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token}"
        )

        current_user_response = self.client.get(
            reverse("api-current-user")
        )

        self.assertEqual(
            current_user_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            current_user_response.data["email"],
            credentials["email"],
        )

        logout_response = self.client.post(
            reverse("api-logout")
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        invalidated_token_response = self.client.get(
            reverse("api-current-user")
        )

        self.assertEqual(
            invalidated_token_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_registration_allows_names_to_be_omitted(self):
        credentials = {
            "email": "api_without_names@example.com",
            "password": "TemporaryTest123!",
        }

        response = self.client.post(
            reverse("api-register"),
            credentials,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = Users.objects.get(email=credentials["email"])
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertTrue(user.check_password(credentials["password"]))
        self.assertNotIn("password", response.data)


class EventApiTests(APITestCase):
    def setUp(self):
        self.user = Users.objects.create_user(
            username="event_api_test@example.com",
            email="event_api_test@example.com",
            password="TemporaryTest123!",
        )
        self.category = Category.objects.create(
            Name="Automated Test Category"
        )
        self.token = Token.objects.create(user=self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

    def test_create_list_search_update_and_retrieve_event(self):
        create_response = self.client.post(
            reverse("api-events"),
            {
                "CategoryID": self.category.CategoryID,
                "Title": "Automated M1 Event",
                "Description": "Fake event for automated API testing.",
                "Location": "Automated Test Room",
                "DateTime": "2026-09-20T18:00:00Z",
                "EventStatus": True,
            },
            format="json",
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            create_response.data["OrganizerID"],
            self.user.pk,
        )

        event_id = create_response.data["EventID"]

        list_response = self.client.get(reverse("api-events"))

        self.assertEqual(
            list_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(list_response.data), 1)

        search_response = self.client.get(
            reverse("api-events"),
            {"q": "automated"},
        )

        self.assertEqual(
            search_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(search_response.data), 1)

        detail_url = reverse(
            "api-event-detail",
            kwargs={"event_id": event_id},
        )

        update_response = self.client.patch(
            detail_url,
            {
                "Title": "Updated Automated M1 Event",
                "Location": "Updated Automated Test Room",
            },
            format="json",
        )

        self.assertEqual(
            update_response.status_code,
            status.HTTP_200_OK,
        )

        retrieve_response = self.client.get(detail_url)

        self.assertEqual(
            retrieve_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            retrieve_response.data["Title"],
            "Updated Automated M1 Event",
        )
        self.assertEqual(
            retrieve_response.data["Location"],
            "Updated Automated Test Room",
        )