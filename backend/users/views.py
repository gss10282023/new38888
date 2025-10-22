import csv

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsPlatformAdmin
from groups.models import Group

from .models import User, UserProfile
from .serializers import (
    AdminUserSerializer,
    AdminUserWriteSerializer,
    UserProfileSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet providing endpoints for the authenticated user to inspect and
    update their profile information.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "put", "patch", "head", "options"]

    @action(detail=False, methods=["get"], url_path="me", url_name="me")
    def me(self, request):
        """Return the authenticated user's data."""
        user = request.user
        UserProfile.objects.get_or_create(user=user)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @me.mapping.put
    @me.mapping.patch
    def update_me(self, request):
        """
        Update the authenticated user's profile data.

        Expected payload format:
        {
            "track": "AUS-NSW",
            "profile": {
                "firstName": "John",
                ...
            }
        }
        """
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        profile_payload = request.data.get("profile")
        if profile_payload is not None and not isinstance(profile_payload, dict):
            return Response(
                {"error": "Profile payload must be an object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_serializer = None
        if profile_payload is not None:
            profile_serializer = UserProfileSerializer(
                profile,
                data=profile_payload,
                partial=True,
            )
            profile_serializer.is_valid(raise_exception=True)

        updated_fields = []
        track = request.data.get("track")
        if track is not None:
            user.track = track
            updated_fields.append("track")

        with transaction.atomic():
            if profile_serializer is not None:
                profile_instance = profile_serializer.save()
                if "first_name" in profile_serializer.validated_data:
                    user.first_name = profile_instance.first_name
                    updated_fields.append("first_name")
                if "last_name" in profile_serializer.validated_data:
                    user.last_name = profile_instance.last_name
                    updated_fields.append("last_name")

            if updated_fields:
                user.save(update_fields=list(set(updated_fields)))

        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPlatformAdmin])
def admin_stats(request):
    """
    Aggregate counts for the admin dashboard widgets.
    """

    track_param = (request.query_params.get("track") or "").strip()

    users_qs = User.objects.all()
    groups_qs = Group.objects.filter(status__iexact="active")

    if track_param and track_param.lower() != "global":
        users_qs = users_qs.filter(track__iexact=track_param)
        groups_qs = groups_qs.filter(track__iexact=track_param)

    non_pending_users_qs = users_qs.exclude(status="pending")

    mentor_qs = users_qs.filter(role="mentor")
    mentor_non_pending_qs = mentor_qs.exclude(status="pending")
    mentor_active_qs = mentor_qs.filter(status="active")
    mentor_pending_qs = mentor_qs.filter(status="pending")

    student_qs = users_qs.filter(role="student")
    student_non_pending_qs = student_qs.exclude(status="pending")
    student_pending_qs = student_qs.filter(status="pending")

    payload = {
        "totalUsers": non_pending_users_qs.count(),
        "activeGroups": groups_qs.count(),
        "mentors": {
            "total": mentor_non_pending_qs.count(),
            "active": mentor_active_qs.count(),
            "pending": mentor_pending_qs.count(),
        },
        "students": {
            "total": student_non_pending_qs.count(),
            "pending": student_pending_qs.count(),
        },
    }

    return Response(payload, status=status.HTTP_200_OK)


class AdminUserViewSet(viewsets.GenericViewSet):
    """
    ViewSet that powers the admin user management table.
    """

    queryset = User.objects.select_related("profile").all()
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    serializer_class = AdminUserSerializer

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return AdminUserWriteSerializer
        if self.action == "retrieve":
            return UserSerializer
        return super().get_serializer_class()

    def _apply_filters(self, queryset, request):
        role = (request.query_params.get("role") or "").strip()
        if role:
            queryset = queryset.filter(role__iexact=role)

        track = (request.query_params.get("track") or "").strip()
        if track and track.lower() != "global":
            queryset = queryset.filter(track__iexact=track)

        status_param = (request.query_params.get("status") or "").strip()
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)

        search = (request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
            )

        return queryset.order_by("first_name", "last_name", "email")

    def list(self, request):
        queryset = self._apply_filters(self.get_queryset(), request)

        paginator = getattr(self, "paginator", None)
        page_size_param = request.query_params.get("page_size")
        if paginator is not None and page_size_param:
            try:
                paginator.page_size = max(1, min(int(page_size_param), 500))
            except (TypeError, ValueError):
                pass

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        output = AdminUserSerializer(user, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        partial = request.method.lower() == "patch"
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        output = UserSerializer(updated_user, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, pk=None):
        user = self.get_object()

        if user.pk == request.user.pk:
            return Response(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if getattr(user, "is_superuser", False):
            return Response(
                {"error": "Cannot delete a superuser account."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["put", "patch"], url_path="status")
    def update_status(self, request, pk=None):
        user = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "Status value is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = {choice[0] for choice in User.STATUS_CHOICES}
        if new_status not in valid_statuses:
            return Response(
                {"error": "Invalid status value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.status != new_status:
            user.status = new_status
            user.save(update_fields=["status"])

        serializer = self.get_serializer(user)
        return Response(
            {"success": True, "user": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="filters")
    def filter_options(self, request):
        """
        Provide available filter values for the admin UI.
        """

        tracks = (
            self.get_queryset()
            .exclude(track__isnull=True)
            .exclude(track__exact="")
            .order_by("track")
            .values_list("track", flat=True)
            .distinct()
        )
        roles = [choice[0] for choice in User.ROLE_CHOICES]
        statuses = [choice[0] for choice in User.STATUS_CHOICES]

        return Response(
            {
                "tracks": list(tracks),
                "roles": roles,
                "statuses": statuses,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """
        Export the filtered user list as a CSV file.
        """

        queryset = self._apply_filters(self.get_queryset(), request)
        queryset = queryset.select_related("profile")

        timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        filename = f"users-export-{timestamp}.csv"

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "ID",
                "Name",
                "Email",
                "Role",
                "Track",
                "Status",
                "First Name",
                "Last Name",
                "Areas of Interest",
                "School Name",
                "Year Level",
                "Country",
                "Region",
                "Availability",
                "Bio",
            ]
        )

        for user in queryset:
            profile = getattr(user, "profile", None)
            writer.writerow(
                [
                    user.id,
                    user.get_full_name() or user.email,
                    user.email,
                    user.role,
                    user.track or "",
                    user.status,
                    getattr(profile, "first_name", "") or "",
                    getattr(profile, "last_name", "") or "",
                    ",".join(getattr(profile, "areas_of_interest", []) or []),
                    getattr(profile, "school_name", "") or "",
                    getattr(profile, "year_level", "") or "",
                    getattr(profile, "country", "") or "",
                    getattr(profile, "region", "") or "",
                    getattr(profile, "availability", "") or "",
                    getattr(profile, "bio", "") or "",
                ]
            )

        return response
