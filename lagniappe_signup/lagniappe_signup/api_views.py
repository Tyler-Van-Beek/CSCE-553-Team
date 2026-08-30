from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.db.models import Q
from django.shortcuts import get_object_or_404

from events.models import Event

from .serializers import (EventApiSerializer,UserRegistrationSerializer, UserLoginSerializer)


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