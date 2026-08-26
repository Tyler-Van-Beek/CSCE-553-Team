from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView
from django.http import HttpResponse
from events.models import Users, Event, Category, Feedback, Registration
from .forms import EventForm, SignUpForm, FeedbackForm
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout,authenticate
from AI_Chatbot.recommend_bot import get_recommendation
from django.contrib import messages
from AI_Chatbot.embed_current_events import populate_index


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
        print("Authenticated user:", sign)
        print("Submitted username:", username)
        print("Submitted password:", password)


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

@login_required(login_url="/signin/")
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
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


def eventForm(request):
    if request.method == "POST":
        organizer = request.POST.get("Organizer")
        category = request.POST.get("Category")
        title = request.POST.get("Title")
        description = request.POST.get("Description")
        location = request.POST.get("Location")
        dateTime = request.POST.get("DateTime")

        organizer = Users.objects.get(UserID=organizer)
        category = Category.objects.get(Name=category)

        event = Event(
            OrganizerID=organizer,
            CategoryID=category,
            Title=title,
            Description=description,
            Location=location,
            DateTime=dateTime,
        )
        event.save()
        messages.success(request, 'Event created!')
        populate_index()

        return redirect("event-list")
    else:
        return HttpResponse("Only POST requests are allowed.", status=405)


class list_event(ListView):
    model = Event
    template_name = "event_list.html"
    context_object_name = "events"
    paginate = 20

@login_required(login_url="/signin/")
def create_reg(request, pk):
    event_id = pk
    if request.method == "POST":
        form = RegForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("registration-list")
    else:
        form = RegForm(request)

    # Fetch Users and Events for the context
    users = Users.objects.all()
    events = Event.objects.all()

    # Pass data to the template
    context = {
        "form": form,
        "Users": users,
        "event": Event.objects.get(EventID=pk)
    }

    return render(request, "create_registration.html", context)


class list_reg(ListView):
    model = Registration
    template_name = "registration_list.html"
    context_object_name = "registrations"
    paginate = 20


@csrf_exempt
def RegForm(request):
    if request.method == "POST":
        userID = request.POST.get("User")
        event = request.POST.get("Event")

        user = Users.objects.get(UserID=userID)
        event = Event.objects.get(EventID=event)

        registration = Registration(UserID=user, EventID=event)
        registration.save()
        messages.success(request, 'Registration complete!')


        return redirect('event-detail', pk = event.EventID)
    else:
        return HttpResponse("Only POST requests are allowed.", status=405)


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


def feedback_form(request):
    if request.method == "POST":
        user = request.POST.get("User")
        event = request.POST.get("Event")
        rating = request.POST.get("rating")
        comments = request.POST.get("comments")

        event = Event.objects.get(EventID=event)
        user = Users.objects.get(UserID=user)

        feedback = Feedback(
            UserID=user, EventID=event, Rating=rating, Comments=comments
        )
        feedback.save()
        messages.success(request, 'Feedback submitted.')

        return redirect("event-detail", pk=event.EventID)
    else:
        return HttpResponse("Only POST requests are allowed.", status=405)


class list_feedback(ListView):
    model = Feedback
    template_name = "feedback_list.html"
    context_object_name = "feedback"
    paginate = 20


def detail_event(request, pk):
    try:
        event = Event.objects.get(EventID=pk)
    except Event.DoesNotExist:
        return HttpResponse("Event Does Not Exist", status=404)
    
    reg = None
    user = None
    is_registered = False
    if request.user.is_authenticated: 
        user = request.user
        is_registered = Registration.objects.filter(EventID=pk, UserID=user.UserID).exists()
        
        if is_registered:
            reg = Registration.objects.get(EventID=pk, UserID=user.UserID)

    return render(request, "event_detail.html", context={
        "event": event,
        "reg": reg,
        "is_registered": is_registered
    })

@login_required(login_url="/signin/")
def update_event(request, pk):
    event = Event.objects.get(EventID=pk)

    if request.method == "POST":
        # Create form or handle form submission logic here
        # If you're using a form, you can validate and save it like this:
        form = EventForm(request.POST, instance=event)

        if form.is_valid():
            print("Form is valid")
            form.save()
            messages.success(request, 'Event Updated.')
            populate_index()
            return redirect("event-detail", pk=event.EventID)
        else:
            print("Form is not valid")
            print(form.errors)

    else:
        # If it's a GET request, prepopulate the form with event data
        form = EventForm(instance=event)

    # Fetch users and categories for context
    users = Users.objects.all()
    category = Category.objects.all()

    # Add the context for the template
    context = {
        "event": event,
        "form": form,
        "Users": users,
        "Category": category,
    }

    return render(request, "event_update.html", context)

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
    try:
        event = Event.objects.get(EventID=pk)
        reg = Registration.objects.filter(EventID=event)
    except Event.DoesNotExist or Registration.DoesNotExist:
        raise HttpResponse("Event or Registration Does Not Exist", status=404)

    return render(
        request,
        "event_registrations.html",
        context={"Registrations": reg, "Event": event},
    )

@login_required(login_url="/signin/")
def event_delete(request, pk):
    eve = get_object_or_404(Event, EventID=pk)
    if request.method == "POST":
        eve.delete()
        messages.error(request, 'Event Deleted.')
        success_url = reverse_lazy("event-list")
        populate_index()
        return redirect(success_url)

    return render(request, "event_delete.html", context={"event": eve})

@csrf_exempt
def chat_response(request):
    if request.method == 'POST':
        msg = request.POST.get('message', '')
        reply = get_recommendation(msg)
        return JsonResponse({'reply': reply})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url="/signin/")
def reg_delete(request, pk):
    reg = get_object_or_404(Registration, RegistrationID=pk)
    if request.method == "POST":
        reg.delete()
        messages.error(request, 'Registration Cancelled.')
        success_url = reverse_lazy("event-detail", kwargs={"pk": reg.EventID.EventID})
        populate_index()
        return redirect(success_url)

    return render(request, "registration_delete.html", context={"reg": reg})
