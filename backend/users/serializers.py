from rest_framework import serializers

from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the user profile with camelCase fields for the API contract.
    """

    firstName = serializers.CharField(
        source="first_name", allow_blank=True, required=False
    )
    lastName = serializers.CharField(
        source="last_name", allow_blank=True, required=False
    )
    areasOfInterest = serializers.ListField(
        source="areas_of_interest",
        child=serializers.CharField(allow_blank=True),
        required=False,
    )
    schoolName = serializers.CharField(
        source="school_name", allow_blank=True, required=False
    )
    yearLevel = serializers.IntegerField(
        source="year_level", allow_null=True, required=False
    )
    country = serializers.CharField(allow_blank=True, required=False)
    region = serializers.CharField(allow_blank=True, required=False)
    availability = serializers.CharField(allow_blank=True, required=False)
    bio = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = UserProfile
        fields = [
            "firstName",
            "lastName",
            "areasOfInterest",
            "schoolName",
            "yearLevel",
            "country",
            "region",
            "availability",
            "bio",
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model including the nested profile payload.
    """

    profile = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "track",
            "status",
            "name",
            "profile",
        ]
        read_only_fields = [
            "email",
            "username",
            "role",
            "track",
            "status",
            "name",
            "profile",
        ]

    def get_profile(self, obj: User) -> dict:
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return UserProfileSerializer(profile).data

    def get_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.email


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for admin-facing user lists.
    """

    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "role",
            "track",
            "status",
        ]
        read_only_fields = [
            "id",
            "name",
            "email",
            "role",
            "track",
            "status",
        ]

    def get_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.email


class AdminUserWriteSerializer(serializers.ModelSerializer):
    """
    Serializer used by admins to create or update users (including profile data).
    """

    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "track",
            "status",
            "profile",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise serializers.ValidationError("Email is required.")

        queryset = User.objects.all()
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized

    def create(self, validated_data: dict) -> User:
        profile_payload = validated_data.pop("profile", None)
        email = validated_data["email"]

        user = User(
            email=email,
            username=email,
            role=validated_data.get("role", "student"),
            track=validated_data.get("track", ""),
            status=validated_data.get("status", "pending"),
        )
        user.set_unusable_password()
        user.save()

        if profile_payload:
            self._update_profile(user, profile_payload)

        return user

    def update(self, instance: User, validated_data: dict) -> User:
        profile_payload = validated_data.pop("profile", None)

        updated_fields: list[str] = []

        email = validated_data.get("email")
        if email and email != instance.email:
            instance.email = email
            instance.username = email
            updated_fields.extend(["email", "username"])

        for field in ["role", "track", "status"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
                updated_fields.append(field)

        if updated_fields:
            instance.save(update_fields=list(set(updated_fields)))

        if profile_payload is not None:
            self._update_profile(instance, profile_payload)

        return instance

    def _update_profile(self, user: User, payload: dict) -> None:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        serializer = UserProfileSerializer(
            profile,
            data=payload,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        profile_instance = serializer.save()

        updated_fields = []
        if "first_name" in serializer.validated_data:
            user.first_name = profile_instance.first_name
            updated_fields.append("first_name")
        if "last_name" in serializer.validated_data:
            user.last_name = profile_instance.last_name
            updated_fields.append("last_name")

        if updated_fields:
            user.save(update_fields=list(set(updated_fields)))
