"""
URL configuration for lagniappe_signup project.

The urlpatterns list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    
Add an import:  from my_app import views
Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    
Add an import:  from other_app.views import Home
Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    
Import the include() function: from django.urls import include, path
Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from . import views
from . import api_views
from events.models import Users, Event, Category, Feedback, Registration
from .views import chat_response
from health_check.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register", api_views.api_register, name="api-register"),
    path("api/auth/login", api_views.api_login, name="api-login"),
    path("api/auth/me", api_views.api_current_user, name="api-current-user"),
    path("api/auth/logout", api_views.api_logout, name="api-logout"),
    path("api/events", api_views.api_events, name="api-events"),
    path("api/events/<int:event_id>",api_views.api_event_detail,name="api-event-detail",),
    path('', views.homepage,name='home'),
    path('about/', views.about,name='about'),
    path('signin/',views.signin,name='signin'),
    path('event/create', views.create_event, name="event-create"),
    path('event/list', views.list_event, name="event-list"),
    path('event/event-list/', views.eventForm, name="event-form"),
    path('event/<int:pk>', views.detail_event, name="event-detail"),
    path('event/update/<int:pk>', views.update_event, name="event-update"),
    path('event/registration/<int:pk>', views.event_registrations, name="event-registrations"),
    path('event/<int:pk>/delete', views.event_delete, name="event-delete"),
    path('registration/create/<int:pk>', views.create_reg, name="registration-create"),
    path('registration/list', views.list_reg.as_view(), name="registration-list"),
    path('registration/create/RegistrationForm/', views.RegForm, name="registration-form"),
    path('registration/delete/<int:pk>', views.reg_delete, name="registration-delete"),
    path('feedback/create/<int:pk>', views.create_feedback, name="feedback-create"),
    path('feedback/list', views.list_feedback.as_view(), name="feedback-list"),
    path('feedback/create/FeedbackForm/', views.feedback_form, name="feedback-form"),
    path('map/', views.eventMap,name='map'),
    path('faq/', views.faq, name='faq'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path('profile/<int:pk>', views.detail_user, name="profile"),
    path('userlist', views.list_users.as_view(), name="user-list"),
    path('chat/', chat_response, name='chat'),
    path("healthcheck/", HealthCheckView.as_view()),
    path("health/", views.health, name="health"),
    ]