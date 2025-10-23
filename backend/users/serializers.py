from rest_framework import serializers

from .models import StudentSupervisor, SupervisorProfile, User, UserProfile


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
    controlledInterests = serializers.ListField(
        source="controlled_interests",
        child=serializers.CharField(allow_blank=True),
        required=False,
    )
    schoolName = serializers.CharField(
        source="school_name", allow_blank=True, required=False
    )
    yearLevel = serializers.IntegerField(
        source="year_level", allow_null=True, required=False
    )
    guardianEmail = serializers.EmailField(
        source="guardian_email", allow_blank=True, required=False
    )
    supervisorEmail = serializers.EmailField(
        source="supervisor_email", allow_blank=True, required=False
    )
    country = serializers.CharField(allow_blank=True, required=False)
    region = serializers.CharField(allow_blank=True, required=False)
    availability = serializers.CharField(allow_blank=True, required=False)
    bio = serializers.CharField(allow_blank=True, required=False)
    joinPermissionGranted = serializers.BooleanField(
        source="join_permission_granted", required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            "firstName",
            "lastName",
            "areasOfInterest",
            "controlledInterests",
            "schoolName",
            "yearLevel",
            "guardianEmail",
            "supervisorEmail",
            "country",
            "region",
            "availability",
            "bio",
            "joinPermissionGranted",
        ]


class SupervisorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for supervisor compliance profile information.
    """

    organization = serializers.CharField(
        source="organisation", allow_blank=True, required=False
    )
    phoneNumber = serializers.CharField(
        source="phone_number", allow_blank=True, required=False
    )
    wwccNumber = serializers.CharField(
        source="wwcc_number", allow_blank=True, required=False
    )
    wwccExpiry = serializers.DateField(
        source="wwcc_expiry", allow_null=True, required=False
    )
    wwccVerified = serializers.BooleanField(
        source="wwcc_verified", required=False
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = SupervisorProfile
        fields = [
            "organization",
            "phoneNumber",
            "wwccNumber",
            "wwccExpiry",
            "wwccVerified",
            "createdAt",
            "updatedAt",
        ]


class SimpleUserSerializer(serializers.ModelSerializer):
    """
    Compact user serializer for nested relationship payloads.
    """

    name = serializers.SerializerMethodField()
    supervisorProfile = SupervisorProfileSerializer(
        source="supervisor_profile", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "track",
            "status",
            "name",
            "supervisorProfile",
        ]
        read_only_fields = fields

    def get_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.email


class StudentSupervisorLinkSerializer(serializers.ModelSerializer):
    """
    Serializer exposing supervisor details for a student.
    """

    relationshipType = serializers.CharField(source="relationship_type")
    joinPermissionGranted = serializers.BooleanField(
        source="join_permission_granted"
    )
    joinPermissionGrantedAt = serializers.DateTimeField(
        source="join_permission_granted_at", allow_null=True
    )
    supervisor = SimpleUserSerializer(read_only=True)

    class Meta:
        model = StudentSupervisor
        fields = [
            "id",
            "relationshipType",
            "joinPermissionGranted",
            "joinPermissionGrantedAt",
            "notes",
            "supervisor",
        ]
        read_only_fields = fields


class StudentSuperviseeLinkSerializer(serializers.ModelSerializer):
    """
    Serializer exposing student details for a supervisor.
    """

    relationshipType = serializers.CharField(source="relationship_type")
    joinPermissionGranted = serializers.BooleanField(
        source="join_permission_granted"
    )
    joinPermissionGrantedAt = serializers.DateTimeField(
        source="join_permission_granted_at", allow_null=True
    )
    student = SimpleUserSerializer(read_only=True)

    class Meta:
        model = StudentSupervisor
        fields = [
            "id",
            "relationshipType",
            "joinPermissionGranted",
            "joinPermissionGrantedAt",
            "notes",
            "student",
        ]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model including nested profile payloads and
    supervisor relationships.
    """

    profile = serializers.SerializerMethodField()
    supervisorProfile = serializers.SerializerMethodField()
    supervisors = serializers.SerializerMethodField()
    supervisees = serializers.SerializerMethodField()
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
            "supervisorProfile",
            "supervisors",
            "supervisees",
        ]
        read_only_fields = [
            "email",
            "username",
            "role",
            "track",
            "status",
            "name",
            "profile",
            "supervisorProfile",
            "supervisors",
            "supervisees",
        ]

    def get_profile(self, obj: User) -> dict:
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return UserProfileSerializer(profile).data

    def get_supervisorProfile(self, obj: User) -> dict | None:
        profile = getattr(obj, "supervisor_profile", None)
        if profile is None:
            return None
        return SupervisorProfileSerializer(profile).data

    def get_supervisors(self, obj: User) -> list[dict]:
        relationships = self._get_prefetched(obj, "supervisor_links")
        if relationships is None:
            queryset = obj.supervisor_links.select_related(
                "supervisor",
                "supervisor__supervisor_profile",
            ).order_by("created_at", "pk")
            relationships = list(queryset)
        else:
            relationships = list(relationships)

        relationships.sort(key=lambda rel: (rel.created_at, rel.pk))
        return StudentSupervisorLinkSerializer(relationships, many=True).data

        return StudentSupervisorLinkSerializer(relationships, many=True).data

    def get_supervisees(self, obj: User) -> list[dict]:
        relationships = self._get_prefetched(obj, "supervisee_links")
        if relationships is None:
            queryset = obj.supervisee_links.select_related(
                "student",
                "student__profile",
            ).order_by("created_at", "pk")
            relationships = list(queryset)
        else:
            relationships = list(relationships)

        relationships.sort(key=lambda rel: (rel.created_at, rel.pk))
        return StudentSuperviseeLinkSerializer(relationships, many=True).data

    def get_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.email

    @staticmethod
    def _get_prefetched(obj: User, attr: str):
        cache = getattr(obj, "_prefetched_objects_cache", None)
        if not cache:
            return None
        return cache.get(attr)


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
    supervisorProfile = SupervisorProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "track",
            "status",
            "profile",
            "supervisorProfile",
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
        supervisor_profile_payload = validated_data.pop("supervisorProfile", None)
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
        if supervisor_profile_payload:
            self._update_supervisor_profile(user, supervisor_profile_payload)

        return user

    def update(self, instance: User, validated_data: dict) -> User:
        profile_payload = validated_data.pop("profile", None)
        supervisor_profile_payload = validated_data.pop("supervisorProfile", None)

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
        if supervisor_profile_payload is not None:
            self._update_supervisor_profile(instance, supervisor_profile_payload)

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

    def _update_supervisor_profile(self, user: User, payload: dict) -> None:
        profile, _ = SupervisorProfile.objects.get_or_create(user=user)
        serializer = SupervisorProfileSerializer(
            profile,
            data=payload,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()


class StudentSupervisorReadSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for administrator views of student-supervisor links.
    """

    student = SimpleUserSerializer(read_only=True)
    supervisor = SimpleUserSerializer(read_only=True)
    relationshipType = serializers.CharField(source="relationship_type")
    joinPermissionGranted = serializers.BooleanField(
        source="join_permission_granted"
    )
    joinPermissionGrantedAt = serializers.DateTimeField(
        source="join_permission_granted_at", allow_null=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = StudentSupervisor
        fields = [
            "id",
            "student",
            "supervisor",
            "relationshipType",
            "joinPermissionGranted",
            "joinPermissionGrantedAt",
            "notes",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields


class StudentSupervisorWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating or updating student-supervisor relationships.
    """

    studentId = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=User.objects.all(),
    )
    supervisorId = serializers.PrimaryKeyRelatedField(
        source="supervisor",
        queryset=User.objects.all(),
    )
    relationshipType = serializers.ChoiceField(
        source="relationship_type",
        choices=StudentSupervisor.RELATIONSHIP_CHOICES,
    )
    joinPermissionGranted = serializers.BooleanField(
        source="join_permission_granted",
        required=False,
    )
    notes = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = StudentSupervisor
        fields = [
            "studentId",
            "supervisorId",
            "relationshipType",
            "joinPermissionGranted",
            "notes",
        ]

    def validate(self, attrs):
        student = attrs["student"]
        supervisor = attrs["supervisor"]

        if student.pk == supervisor.pk:
            raise serializers.ValidationError(
                {"supervisorId": "Student and supervisor must be different users."}
            )

        if getattr(student, "role", "") != "student":
            raise serializers.ValidationError(
                {"studentId": "Selected user is not registered as a student."}
            )

        if getattr(supervisor, "role", "") not in {"supervisor", "mentor", "admin"}:
            raise serializers.ValidationError(
                {"supervisorId": "Supervisor must have role supervisor, mentor, or admin."}
            )

        return attrs

    def create(self, validated_data):
        join_permission = validated_data.pop("join_permission_granted", False)
        instance = super().create(validated_data)
        instance.set_join_permission(join_permission)
        if join_permission:
            instance.save(update_fields=["join_permission_granted", "join_permission_granted_at", "updated_at"])
        return instance

    def update(self, instance, validated_data):
        join_permission = validated_data.pop("join_permission_granted", None)
        instance = super().update(instance, validated_data)
        if join_permission is not None:
            previous = instance.join_permission_granted
            instance.set_join_permission(join_permission)
            fields = ["join_permission_granted", "join_permission_granted_at", "updated_at"]
            if previous != join_permission:
                instance.save(update_fields=fields)
        return instance


class StudentSupervisorSelfUpdateSerializer(serializers.Serializer):
    """
    Serializer used by students/supervisors to toggle join permission.
    """

    joinPermissionGranted = serializers.BooleanField()

    def update(self, instance: StudentSupervisor, validated_data: dict) -> StudentSupervisor:
        granted = validated_data["joinPermissionGranted"]
        previous = instance.join_permission_granted
        instance.set_join_permission(granted)
        if previous != instance.join_permission_granted:
            instance.save(update_fields=["join_permission_granted", "join_permission_granted_at", "updated_at"])
        return instance

    def create(self, validated_data):
        raise NotImplementedError("Creation is not supported via this serializer.")
