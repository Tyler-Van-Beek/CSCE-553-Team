from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView
from django.http import HttpResponse, JsonResponse
from events.models import Users, Event, Category, Feedback, Registration
from .forms import EventForm, SignUpForm, FeedbackForm
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout,authenticate
from AI_Chatbot.recommend_bot import get_recommendation
from django.contrib import messages
from AI_Chatbot.embed_current_events import populate_index
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from .serializers import EventSerializer
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import connections, transaction
from django.http import Http404

from .registration_service import register_on_event_shard
from .shard_routing import shard_for_event
from .event_service import create_event_on_shard, update_event_on_shard, delete_event_on_shard

logger = logging.getLogger(__name__)
def health(request):
    return JsonResponse({"status": "ok"})

def homepage(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def faq(request):
    return render(request, "faq.html")


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        sign = authenticate(username=username, password=password)


        if sign is not None:
            login(request, sign)
            messages.success(request, 'Logged in')
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('home')
        else:
            messages.error(request, 'Incorrect login information')
    return render(request, "signin.html")

def signout(request):
    logout(request)
    messages.success(request, 'Signed out')
    return redirect('home')


def eventMap(request):
    return render(request, "eventMap.html")

def save_browser_event(event, organizer):
    if {"shard_0", "shard_1"}.issubset(connections.databases):
        return create_event_on_shard(
            organizer_id=organizer.pk,
            category_id=event.CategoryID_id,
            Title=event.Title,
            Description=event.Description,
            Location=event.Location,
            DateTime=event.DateTime or None,
            EventStatus=event.EventStatus,
        )

    event.OrganizerID = organizer
    event.save()
    return event

@login_required(login_url="/signin/")
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            save_browser_event(form.save(commit=False), request.user)
            return redirect("event-list")
    else:
        form = EventForm(request)

    # Fetch Users and Events for the context
    users = Users.objects.all()
    category = Category.objects.all()

    # Pass data to the template
    context = {
        "form": form,
        "Users": users,
        "Category": category,
    }

    return render(request, "create_event.html", context)

@login_required(login_url="/signin/")
def eventForm(request):
    if request.method == "POST":
        #organizer = request.POST.get("Organizer")
        organizer = request.user  # Use the logged-in user's ID as the organizer
        category = request.POST.get("Category")
        title = request.POST.get("Title")
        description = request.POST.get("Description")
        location = request.POST.get("Location")
        dateTime = request.POST.get("DateTime")

        #organizer = Users.objects.get(UserID=organizer)
        category = Category.objects.get(Name=category)

        event = Event(
            OrganizerID=organizer,
            CategoryID=category,
            Title=title,
            Description=description,
            Location=location,
            DateTime=dateTime,
        )
        save_browser_event(event, request.user)
        messages.success(request, 'Event created!')

        return redirect("event-list")
    else:
        return HttpResponse("Only POST requests are allowed.", status=405)

@csrf_exempt
def list_event(request):
    if request.method == "GET":
        eve = Event.objects.all().select_related("CategoryID").order_by('EventID')
        serializer = EventSerializer(eve, many=True)

        paginator = Paginator(eve, 30)

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        events = list(page_obj.object_list)

        return render(
            request,
            "event_list.html",
            {"events": events,"page_obj": page_obj}
        )
    
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

@login_required(login_url="/signin/")
def create_reg(request, pk):
    sharding_enabled = {"shard_0", "shard_1"}.issubset(connections.databases)

    if request.method == "POST":
        if sharding_enabled:
            try:
                _, created = register_on_event_shard(
                    event_id=pk, user_id=request.user.pk
                )
            except Event.DoesNotExist as exc:
                raise Http404("Event not found.") from exc
        else:
            event = get_object_or_404(Event, pk=pk)
            _, created = Registration.objects.get_or_create(
                EventID_id=event.pk, UserID_id=request.user.pk
            )

        if created:
            messages.success(request, "Registration complete!")
        else:
            messages.info(request, "You are already registered for this event.")

        return redirect("event-detail", pk=pk)

    events = Event.objects.all()
    if sharding_enabled:
        events = events.using(shard_for_event(pk))

    event = get_object_or_404(events, pk=pk)
    return render(request, "create_registration.html", {"event": event})


class list_reg(ListView):
    model = Registration
    template_name = "registration_list.html"
    context_object_name = "registrations"
    paginate = 20


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created. Please sign in')
            return redirect("signin")
    else:
        form = SignUpForm(request)

    return render(request, "create_user.html")


def signupform(request):
    if request.method == "POST":
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")
        Username = request.POST.get("username")
        Email = request.POST.get("email")
        Password = request.POST.get("password")

        user = Users(
            first_name=firstname,
            last_name=lastname,
            username=Username,
            email=Email,
            password=Password,
        )
        user.save()
        messages.success(request, 'User created. Please sign in.')

        return redirect("home")
    else:
        return HttpResponse("Only POST requests are allowed.", status=405)

@login_required(login_url="/signin/")
def create_feedback(request, pk):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Feedback submitted.')
            return redirect("event-detail", pk=pk)
    else:
        form = FeedbackForm(request)

    # Fetch Users and Events for the context
    users = Users.objects.all()

    # Pass data to the template
    context = {
        "form": form,
        "Users": users,
        "event": Event.objects.get(EventID=pk)
    }

    return render(request, "create_feedback.html", context)


@login_required(login_url="/signin/")
def feedback_form(request):
    if request.method != "POST":
        return HttpResponse("Only POST requests are allowed.", status=405)

    try:
        event_id = int(request.POST.get("Event", ""))
        rating = int(request.POST.get("rating", ""))
    except ValueError:
        return HttpResponse("Enter a valid event and rating.", status=400)

    comments = request.POST.get("comments", "").strip()
    if not (1 <= event_id <= 2_147_483_647 and 1 <= rating <= 5 and 1 <= len(comments) <= 500):
        return HttpResponse("Enter a valid event, rating, and comments.", status=400)

    alias = "default"
    if {"shard_0", "shard_1"}.issubset(connections.databases):
        alias = shard_for_event(event_id)

    user_id = request.user.pk

    with transaction.atomic(using=alias):
        event = get_object_or_404(Event.objects.using(alias), pk=event_id)

        if alias != "default":
            with connections[alias].cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO m6_user_reference ("UserID")
                    VALUES (%s)
                    ON CONFLICT ("UserID") DO NOTHING
                    """,
                    [user_id],
                )

        _, created = Feedback.objects.using(alias).get_or_create(
            EventID_id=event.pk,
            UserID_id=user_id,
            defaults={"Rating": rating, "Comments": comments},
        )

    if created:
        messages.success(request, "Feedback submitted.")
    else:
        messages.info(request, "You already submitted feedback for this event.")

    return redirect("event-detail", pk=event_id)


class list_feedback(ListView):
    model = Feedback
    template_name = "feedback_list.html"
    context_object_name = "feedback"
    paginate_by = 20

    def get_queryset(self):
        feedback = Feedback.objects.select_related("EventID").order_by("-Date", "-pk")
        if {"shard_0", "shard_1"}.issubset(connections.databases):
            return sorted(
                (
                    row
                    for alias in ("shard_0", "shard_1")
                    for row in feedback.using(alias)
                ),
                key=lambda row: (row.Date, row.pk, row.EventID_id),
                reverse=True,
            )
        return feedback

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_rows = list(context["feedback"])
        users = Users.objects.using("default").in_bulk(
            {row.UserID_id for row in page_rows}
        )
        for row in page_rows:
            user = users.get(row.UserID_id)
            row.feedback_username = user.username if user else "Unknown user"
        context["feedback"] = page_rows
        return context


def detail_event(request, pk):
    alias = "default"
    if {"shard_0", "shard_1"}.issubset(connections.databases):
        alias = shard_for_event(pk)

    event = get_object_or_404(
        Event.objects.using(alias).select_related("CategoryID"),
        pk=pk,
    )
    organizer = Users.objects.using("default").filter(
        pk=event.OrganizerID_id,
    ).first()
    organizer_name = (
        organizer.get_full_name() or organizer.email
        if organizer else "Unknown organizer"
    )

    reg = None
    if request.user.is_authenticated:
        reg = Registration.objects.using(alias).filter(
            EventID_id=pk,
            UserID_id=request.user.pk,
        ).first()

    return render(request, "event_detail.html", {
        "event": event,
        "reg": reg,
        "is_registered": reg is not None,
        "organizer_name": organizer_name,
        "is_organizer": (
            request.user.is_authenticated
            and request.user.pk == event.OrganizerID_id
        ),
    })

@login_required(login_url="/signin/")
def update_event(request, pk):
    sharding_enabled = {"shard_0", "shard_1"}.issubset(connections.databases)
    events = Event.objects.all()
    if sharding_enabled:
        events = events.using(shard_for_event(pk))

    event = get_object_or_404(events, pk=pk)
    if event.OrganizerID_id != request.user.pk:
        return HttpResponse("You can update only events you organize.", status=403)

    if request.method == "POST":
        if sharding_enabled:
            form = EventForm(request.POST)
        else:
            form = EventForm(request.POST, instance=event)
        form.fields.pop("OrganizerID")

        if form.is_valid():
            if sharding_enabled:
                update_event_on_shard(event=event, changes=form.cleaned_data)
            else:
                form.save()

            messages.success(request, "Event Updated.")
            return redirect("event-detail", pk=event.pk)
    else:
        form = EventForm(instance=event)
        form.fields.pop("OrganizerID")

    return render(
        request,
        "event_update.html",
        {
            "event": event,
            "form": form,
            "Category": Category.objects.all(),
        },
    )

@login_required(login_url="/signin/")
def detail_user(request, pk):
    try:
        user = Users.objects.get(UserID=pk)
    except Event.DoesNotExist:
        raise HttpResponse("User Does Not Exist", status=404)

    return render(request, "user_detail.html", context={"User": user})


class list_users(ListView):
    model = Users
    template_name = "user_list.html"
    context_object_name = "User"
    paginate = 20

@login_required(login_url="/signin/")
def event_registrations(request, pk):
    alias = "default"
    if {"shard_0", "shard_1"}.issubset(connections.databases):
        alias = shard_for_event(pk)

    event = get_object_or_404(Event.objects.using(alias), pk=pk)
    registrations = list(
        Registration.objects.using(alias)
        .filter(EventID_id=pk)
        .order_by("RegistrationID")
    )

    user_ids = {registration.UserID_id for registration in registrations}
    users = Users.objects.using("default").in_bulk(user_ids)
    for registration in registrations:
        user = users.get(registration.UserID_id)
        registration.attendee_username = user.username if user else "Unknown user"

    return render(
        request,
        "event_registrations.html",
        {"Registrations": registrations, "Event": event},
    )

@login_required(login_url="/signin/")
def event_delete(request, pk):
    sharding_enabled = {"shard_0", "shard_1"}.issubset(connections.databases)
    events = Event.objects.all()
    if sharding_enabled:
        events = events.using(shard_for_event(pk))

    event = get_object_or_404(events, pk=pk)
    if event.OrganizerID_id != request.user.pk:
        return HttpResponse("You can delete only events you organize.", status=403)

    if request.method == "POST":
        if sharding_enabled:
            delete_event_on_shard(event=event)
        else:
            event.delete()

        messages.success(request, "Event deleted.")
        return redirect("event-list")

    return render(request, "event_delete.html", {"event": event})

@csrf_exempt
def chat_response(request):
    if request.method == 'POST':
        msg = request.POST.get('message', '')
        reply = get_recommendation(msg)
        return JsonResponse({'reply': reply})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url="/signin/")
def reg_delete(request, event_id, registration_id):
    #user = request.user

    registrations = Registration.objects.all()
    if {"shard_0", "shard_1"}.issubset(connections.databases):
        registrations = registrations.using(shard_for_event(event_id))

    reg = get_object_or_404(
        registrations,
        RegistrationID=registration_id,
        EventID_id=event_id,
        UserID_id=request.user.pk,
    )

    if request.method == "POST":
        reg.delete(using=registrations.db)

        messages.error(request, "Registration Cancelled.")
        return redirect("event-detail", pk=event_id)

    return render(
        request,
        "registration_delete.html",
        {"reg": reg}
    )
