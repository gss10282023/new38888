from typing import Any

from rest_framework import serializers

from users.models import User

from .models import Group, GroupMember, Milestone, Task


class UserNameMixin:
    """
    Shared helper to format the display name for users.
    """

    @staticmethod
    def get_display_name(user: User) -> str:
        full_name = user.get_full_name()
        return full_name if full_name else user.email


class GroupMentorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class GroupSummarySerializer(serializers.ModelSerializer, UserNameMixin):
    """
    Slim serializer for listing groups.
    """

    members = serializers.SerializerMethodField()
    mentor = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "members",
            "status",
            "mentor",
            "track",
        ]

    def get_members(self, obj: Group) -> int:
        annotated_count = getattr(obj, "member_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.members.count()

    def get_mentor(self, obj: Group) -> dict[str, Any] | None:
        mentor = obj.mentor
        if mentor is None:
            return None
        return {
            "id": mentor.id,
            "name": self.get_display_name(mentor),
        }


class GroupMemberSerializer(serializers.ModelSerializer, UserNameMixin):
    """
    Serializer for the group membership relation.
    """

    id = serializers.IntegerField(source="user.id")
    name = serializers.SerializerMethodField()

    class Meta:
        model = GroupMember
        fields = [
            "id",
            "name",
            "role",
        ]

    def get_name(self, obj: GroupMember) -> str:
        return self.get_display_name(obj.user)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "name",
            "completed",
        ]
        read_only_fields = [
            "id",
            "name",
            "completed",
        ]


class TaskCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Task name cannot be empty.")
        return value


class TaskUpdateSerializer(serializers.Serializer):
    completed = serializers.BooleanField()


class MilestoneSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Milestone
        fields = [
            "id",
            "title",
            "tasks",
        ]


class GroupDetailSerializer(GroupSummarySerializer):
    members = GroupMemberSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)

    class Meta(GroupSummarySerializer.Meta):
        fields = GroupSummarySerializer.Meta.fields + ["members", "milestones"]


class GroupMemberCreateSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
    role = serializers.CharField(max_length=20, required=False, allow_blank=True)


class GroupCreateSerializer(serializers.Serializer):
    groupId = serializers.CharField(
        max_length=50, required=False, allow_blank=True, allow_null=True
    )
    name = serializers.CharField(max_length=255)
    track = serializers.CharField(max_length=50, required=False, allow_blank=True)
    status = serializers.CharField(max_length=50, required=False, allow_blank=True)
    mentorId = serializers.IntegerField(required=False, allow_null=True)
    members = GroupMemberCreateSerializer(many=True, required=False)

    def validate_groupId(self, value: str | None) -> str | None:
        if not value:
            return None
        group_id = value.strip()
        if not group_id:
            return None
        if Group.objects.filter(pk=group_id).exists():
            raise serializers.ValidationError("Group ID already exists.")
        return group_id

    def validate_mentorId(self, value: int | None) -> int | None:
        if value is None:
            return None
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Mentor not found.")
        return value

    def validate_members(self, value):
        if not value:
            raise serializers.ValidationError("At least one member is required.")

        user_ids = []
        seen = set()
        for item in value:
            user_id = item.get("userId")
            if user_id in seen:
                raise serializers.ValidationError("Duplicate member detected.")
            seen.add(user_id)
            user_ids.append(user_id)

        existing_ids = set(
            User.objects.filter(id__in=user_ids).values_list("id", flat=True)
        )
        missing = [user_id for user_id in user_ids if user_id not in existing_ids]
        if missing:
            missing_str = ", ".join(str(uid) for uid in missing)
            raise serializers.ValidationError(
                f"User ID(s) {missing_str} do not exist."
            )

        normalised = []
        for item in value:
            normalised.append(
                {
                    "userId": item.get("userId"),
                    "role": (item.get("role") or "student").strip() or "student",
                }
            )

        return normalised
