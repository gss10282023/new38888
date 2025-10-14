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
