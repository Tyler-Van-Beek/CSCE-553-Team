"""
URL configuration for lagniappe_signup project.

The urlpatterns list routes URLs to views.
For more information:
https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include

from . import views
from . import api_views
from .views import chat_response

from health_check.views import HealthCheckView


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Authentication APIs
    path(
        "api/auth/register",
        api_views.api_register,
        name="api-register",
    ),
    path(
        "api/auth/login",
        api_views.api_login,
        name="api-login",
    ),
    path(
        "api/auth/me",
        api_views.api_current_user,
        name="api-current-user",
    ),
    path(
        "api/auth/logout",
        api_views.api_logout,
        name="api-logout",
    ),

    # Event APIs
    path(
        "api/events",
        api_views.api_events,
        name="api-events",
    ),
    path(
        "api/events/<int:event_id>",
        api_views.api_event_detail,
        name="api-event-detail",
    ),

    # Registration APIs
    # Current logged-in user's registrations
    path(
        "api/registrations",
        api_views.api_registrations,
        name="api-registrations",
    ),

    # Delete a registration belonging to the logged-in user
    path(
        "api/registrations/delete/<int:event_id>/<int:registration_id>",
        api_views.api_registration_detail,
        name="api-registration-detail",
    ),

    # M4 two-table API
    path(
        "api/registrations-with-events",
        api_views.api_registrations_with_events,
        name="api-registrations-with-events",
    ),

    # M4 three-table API
    path(
        "api/registrations-with-event-category",
        api_views.api_registrations_with_event_category,
        name="api-registrations-with-event-category",
    ),

    # M4 event registration OFFSET pagination
    path(
        "api/events/<int:event_id>/registrations",
        api_views.api_event_registrations,
        name="api-event-registrations",
    ),

    # M4 event registration keyset pagination
    path(
        "api/events/<int:event_id>/registrations-keyset",
        api_views.api_event_registrations_keyset,
        name="api-event-registrations-keyset",
    ),

    # Web application pages
    path(
        "",
        views.homepage,
        name="home",
    ),
    path(
        "about/",
        views.about,
        name="about",
    ),
    path(
        "signin/",
        views.signin,
        name="signin",
    ),

    # Event pages
    path(
        "event/create",
        views.create_event,
        name="event-create",
    ),
    path(
        "event/list",
        views.list_event,
        name="event-list",
    ),
    path(
        "event/event-list/",
        views.eventForm,
        name="event-form",
    ),
    path(
        "event/<int:pk>",
        views.detail_event,
        name="event-detail",
    ),
    path(
        "event/update/<int:pk>",
        views.update_event,
        name="event-update",
    ),
    path(
        "event/registration/<int:pk>",
        views.event_registrations,
        name="event-registrations",
    ),
    path(
        "event/<int:pk>/delete",
        views.event_delete,
        name="event-delete",
    ),

    # Registration pages
    path(
        "registration/create/<int:pk>",
        views.create_reg,
        name="registration-create",
    ),
    path(
        "registration/list",
        views.list_reg.as_view(),
        name="registration-list",
    ),
    path(
        "registration/create/RegistrationForm/",
        views.RegForm,
        name="registration-form",
    ),
    path(
        "registration/delete/<int:event_id>/<int:registration_id>",
        views.reg_delete,
        name="registration-delete",
    ),

    # Feedback pages
    path(
        "feedback/create/<int:pk>",
        views.create_feedback,
        name="feedback-create",
    ),
    path(
        "feedback/list",
        views.list_feedback.as_view(),
        name="feedback-list",
    ),
    path(
        "feedback/create/FeedbackForm/",
        views.feedback_form,
        name="feedback-form",
    ),

    # Other pages
    path(
        "map/",
        views.eventMap,
        name="map",
    ),
    path(
        "faq/",
        views.faq,
        name="faq",
    ),
    path(
        "signup/",
        views.signup,
        name="signup",
    ),
    path(
        "signout/",
        views.signout,
        name="signout",
    ),
    path(
        "profile/<int:pk>",
        views.detail_user,
        name="profile",
    ),
    path(
        "userlist",
        views.list_users.as_view(),
        name="user-list",
    ),
    path(
        "chat/",
        chat_response,
        name="chat",
    ),

    # Health checks
    path(
        "healthcheck/",
        HealthCheckView.as_view(),
    ),
    path(
        "health/",
        views.health,
        name="health",
    ),
]