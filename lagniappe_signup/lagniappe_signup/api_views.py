import os
from rest_framework import status, serializers
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

from events.models import Event, Registration, EventSearch

from .serializers import (
    EventApiSerializer,
    RegistrationApiSerializer,
    RegistrationWithEventSerializer,
    RegistrationWithEventCategorySerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    EventSearchSerializer
)
from django.db.models import F, Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from django.http import JsonResponse
from openai import OpenAI
from pgvector.django import CosineDistance


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

class SearchPagination(PageNumberPagination):
    page_size=30
    page_size_query_param = 'page_size'

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def search_api(request):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    q = request.GET.get("q", "").strip()[:200]
    cat = request.GET.get("Category", "").strip()
    
    results = EventSearch.objects.all()
    facets = []

    if q:
        # 1. Baseline Typo Tolerance Text Similarity
        results = results.annotate(
            title_sim=TrigramSimilarity("Title", q),
            desc_sim=TrigramSimilarity("Description", q),
            loc_sim=TrigramSimilarity("Location", q),
        ).annotate(
            text_sim=F("title_sim") * 2.0 + F("desc_sim") * 0.5 + F("loc_sim") * 0.5
        )

        try:
            # 2. Vector Embedding Generation
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=q,
                dimensions=738
            )
            query_vector = response.data[0].embedding
                    
            # 3. Hybrid Merge (Text Match Score + Semantic Distance)
            results = results.exclude(Embedding__isnull=True).annotate(
                cosine_dist=CosineDistance("Embedding", query_vector)
            ).annotate(
                hybrid_rank=(F("text_sim") * 1.5) + (1.0 - F("cosine_dist"))
            )

            # Filter out non-relevance noise
            results = results.filter(text_sim__gt=0.05) | results.filter(cosine_dist__lt=0.70)
            results = results.order_by("-hybrid_rank", "Id")
            
        except Exception as e:
            print(f"Embedding or query failed: {e}")
            # Safe text-only fallback if OpenAI breaks down
            results = results.filter(text_sim__gt=0.1).order_by("-text_sim", "Id")

        # 4. Generate Category counts BEFORE slicing for pagination
        facets_queryset = (
            results.order_by()
            .values("Category")
            .exclude(Category__isnull=True)
            .exclude(Category="")
            .annotate(n=Count("Id"))
            .order_by("-n")
        )
        facets = list(facets_queryset)

        # 5. Filter items down by category selection
        if cat:
            results = results.filter(Category=cat)
    else:
        results = EventSearch.objects.none()

    # 6. Apply DRF Pagination
    paginator = SearchPagination()
    paginated_results = paginator.paginate_queryset(results, request)
    
    # 7. Serialize the records to JSON
    serializer = EventSearchSerializer(paginated_results, many=True)

    # 8. Return data payload along with your faceted sidebar meta metrics
    return Response({
        "count": paginator.page.paginator.count,
        "next": paginator.get_next_link(),
        "previous": paginator.get_previous_link(),
        "q": q,
        "facets": facets,
        "results": serializer.data
    })