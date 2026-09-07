from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.db.models import Q
from django.shortcuts import get_object_or_404

from events.models import Event, Registration

from .serializers import (EventApiSerializer,RegistrationApiSerializer,UserRegistrationSerializer, UserLoginSerializer)


@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    return Response(
        {
            "user_id": user.UserID,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    serializer = UserLoginSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    token, created = Token.objects.get_or_create(user=user)

    return Response(
        {
            "token": token.key,
            "user_id": user.UserID,
            "email": user.email,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_current_user(request):
    return Response(
        {
            "user_id": request.user.UserID,
            "email": request.user.email,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_logout(request):
    request.auth.delete()

    return Response(
        {"detail": "Logged out successfully."},
        status=status.HTTP_200_OK,
    )


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_events(request):
    if request.method == "GET":
        events = Event.objects.all().order_by("EventID")

        search_term = request.query_params.get("q", "").strip()
        if search_term:
            events = events.filter(
                Q(Title__icontains=search_term)
                | Q(Description__icontains=search_term)
                | Q(Location__icontains=search_term)
            )

        serializer = EventApiSerializer(events, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    serializer = EventApiSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    event = serializer.save(OrganizerID=request.user)

    return Response(
        EventApiSerializer(event).data,
        status=status.HTTP_201_CREATED,
    )

@api_view(["GET", "PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_event_detail(request, event_id):
    event = get_object_or_404(Event, EventID=event_id)

    if request.method == "GET":
        return Response(
            EventApiSerializer(event).data,
            status=status.HTTP_200_OK,
        )

    if event.OrganizerID_id != request.user.pk:
        return Response(
            {
                "detail": (
                    "You can update only events that you organize."
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = EventApiSerializer(
        event,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )

@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_registrations(request):
    if request.method == "GET":
        registrations = Registration.objects.filter(
            UserID=request.user
        ).order_by("RegistrationID")

        return Response(
            RegistrationApiSerializer(
                registrations,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    serializer = RegistrationApiSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    event = serializer.validated_data["EventID"]

    if Registration.objects.filter(
        UserID=request.user,
        EventID=event,
    ).exists():
        return Response(
            {
                "detail": (
                    "You are already registered for this event."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    registration = serializer.save(UserID=request.user)

    return Response(
        RegistrationApiSerializer(registration).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_registration_detail(request, registration_id):
    registration = get_object_or_404(
        Registration,
        RegistrationID=registration_id,
    )

    if registration.UserID_id != request.user.pk:
        return Response(
            {
                "detail": (
                    "You can cancel only your own registration."
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    registration.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)