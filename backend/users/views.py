from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User, UserProfile
from .serializers import UserProfileSerializer, UserSerializer


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
