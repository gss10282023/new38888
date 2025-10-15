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
