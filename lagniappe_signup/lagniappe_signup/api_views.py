from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination

from django.db.models import Q
from django.shortcuts import get_object_or_404

from events.models import Event, Registration

from .serializers import (
    EventApiSerializer,
    RegistrationApiSerializer,
    RegistrationWithEventSerializer,
    RegistrationWithEventCategorySerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
)


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

        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(events, request)
        serializer = EventApiSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

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
    """
    GET:
    Return registrations belonging to the logged-in user.

    POST:
    Register the logged-in user for an event.
    """

    if request.method == "GET":
        registrations = (
            Registration.objects
            .filter(UserID=request.user)
            .order_by("RegistrationID")
        )

        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(
            registrations,
            request,
        )

        serializer = RegistrationApiSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    serializer = RegistrationApiSerializer(
        data=request.data
    )
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

    registration = serializer.save(
        UserID=request.user
    )

    return Response(
        RegistrationApiSerializer(registration).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_registration_detail(
    request,
    event_id,
    registration_id,
):
    registration = get_object_or_404(
        Registration.objects.select_related(
            "UserID",
            "EventID",
        ),
        RegistrationID=registration_id,
        EventID_id=event_id,
        UserID=request.user,
    )

    registration.delete()

    return Response(
        status=status.HTTP_204_NO_CONTENT
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_registrations_with_events(request):
    """
    M4 two-table query:
    Registration -> Event
    """

    registrations = (
        Registration.objects
        .filter(UserID=request.user)
        .select_related("EventID")
        .order_by("RegistrationID")
    )

    print(registrations.query)

    paginator = PageNumberPagination()
    paginator.page_size = 20

    page = paginator.paginate_queryset(
        registrations,
        request,
    )

    serializer = RegistrationWithEventSerializer(
        page,
        many=True,
    )

    return paginator.get_paginated_response(
        serializer.data
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_registrations_with_event_category(request):
    """
    M4 three-table query:
    Registration -> Event -> Category
    """

    registrations = (
        Registration.objects
        .filter(UserID=request.user)
        .select_related(
            "EventID",
            "EventID__CategoryID",
        )
        .order_by("RegistrationID")
    )

    print(registrations.query)

    paginator = PageNumberPagination()
    paginator.page_size = 20

    page = paginator.paginate_queryset(
        registrations,
        request,
    )

    serializer = RegistrationWithEventCategorySerializer(
        page,
        many=True,
    )

    return paginator.get_paginated_response(
        serializer.data
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_event_registrations(request, event_id):
    """
    M4 OFFSET/page-number pagination.

    Example:
    /api/events/2464/registrations?page=251
    """

    registrations = (
        Registration.objects
        .filter(EventID_id=event_id)
        .order_by("RegistrationID")
    )

    paginator = PageNumberPagination()
    paginator.page_size = 20

    page = paginator.paginate_queryset(
        registrations,
        request,
    )

    serializer = RegistrationApiSerializer(
        page,
        many=True,
    )

    return paginator.get_paginated_response(
        serializer.data
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_event_registrations_keyset(
    request,
    event_id,
):
    """
    M4 keyset/cursor pagination.

    Example:
    /api/events/2464/registrations-keyset?after=133019
    """

    page_size = 20

    registrations = (
        Registration.objects
        .filter(EventID_id=event_id)
        .order_by("RegistrationID")
    )

    after = request.query_params.get("after")

    if after:
        registrations = registrations.filter(
            RegistrationID__gt=after
        )

    registrations = list(
        registrations[:page_size + 1]
    )

    has_more = len(registrations) > page_size
    page = registrations[:page_size]

    serializer = RegistrationApiSerializer(
        page,
        many=True,
    )

    next_cursor = None

    if has_more and page:
        next_cursor = page[-1].RegistrationID

    return Response(
        {
            "next_cursor": next_cursor,
            "results": serializer.data,
        }
    )