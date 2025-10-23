from django.db import transaction
from django.db.models import Count, Q, Max
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsPlatformAdmin
from users.models import User

from .models import Group, GroupMember, Milestone, Task
from .serializers import (
    GroupCreateSerializer,
    GroupDetailSerializer,
    GroupSummarySerializer,
    MilestoneCreateSerializer,
    MilestoneSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)


class GroupViewSet(viewsets.GenericViewSet):
    """
    ViewSet providing endpoints for listing a user's groups, retrieving details,
    and managing milestone tasks within a group.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = GroupSummarySerializer

    def get_queryset(self):
        user = self.request.user
        base_queryset = Group.objects.select_related("mentor").prefetch_related(
            "members__user",
            "milestones__tasks",
        )

        if not user.is_authenticated:
            return base_queryset.none()

        # Admins and supervisors can see all groups
        if getattr(user, "role", None) in {"admin", "supervisor"} or user.is_staff:
            return base_queryset

        return base_queryset.filter(
            Q(members__user=user) | Q(mentor=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return GroupDetailSerializer
        if self.action == "create":
            return GroupCreateSerializer
        if self.action in {"add_task", "update_task"}:
            return TaskSerializer
        return GroupSummarySerializer

    def list(self, request, *args, **kwargs):
        """
        Return the list of groups accessible to the authenticated user.
        Admins/supervisors receive all groups, other users see only their own groups.
        """
        queryset = self.filter_queryset(self.get_queryset())

        track = (request.query_params.get("track") or "").strip()
        if track and track.lower() != "global":
            queryset = queryset.filter(track__iexact=track)

        status_param = (request.query_params.get("status") or "").strip()
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"groups": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="my-groups")
    def my_groups(self, request):
        """
        Return the groups the authenticated user belongs to or mentors.
        """
        queryset = (
            self.get_queryset()
            .filter(Q(members__user=request.user) | Q(mentor=request.user))
            .annotate(member_count=Count("members", distinct=True))
            .distinct()
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({"groups": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        Return the detail for a specific group, including members and milestones.
        """
        group = self.get_object()
        serializer = self.get_serializer(group)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"milestones/(?P<milestone_id>[^/.]+)/tasks",
    )
    def add_task(self, request, pk=None, milestone_id=None):
        """
        Add a task to a milestone within the group.
        """
        group = self.get_object()
        milestone = get_object_or_404(group.milestones, pk=milestone_id)

        input_serializer = TaskCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        task = milestone.tasks.create(
            name=input_serializer.validated_data["name"],
            completed=False,
        )
        output_serializer = TaskSerializer(task)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["put"],
        url_path=r"tasks/(?P<task_id>[^/.]+)",
    )
    def update_task(self, request, pk=None, task_id=None):
        """
        Update the completion state of a task within the group.
        """
        group = self.get_object()
        task = get_object_or_404(Task, pk=task_id, milestone__group=group)

        input_serializer = TaskUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        task.completed = input_serializer.validated_data["completed"]
        task.save(update_fields=["completed"])

        output_serializer = TaskSerializer(task)
        return Response(
            {"success": True, "task": output_serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="milestones")
    def create_milestone(self, request, pk=None):
        """
        Create a new milestone for the specified group.
        """
        group = self.get_object()

        if not self._user_can_manage_group(request.user, group):
            return Response(
                {"error": "You do not have permission to add milestones."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MilestoneCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        max_order = group.milestones.aggregate(max_order=Max("order_index"))["max_order"]
        milestone = group.milestones.create(
            title=serializer.validated_data["title"].strip(),
            description=serializer.validated_data.get("description", ""),
            order_index=(max_order or 0) + 1,
        )

        output_serializer = MilestoneSerializer(milestone)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"milestones/(?P<milestone_id>[^/.]+)",
    )
    def delete_milestone(self, request, pk=None, milestone_id=None):
        """
        Delete a milestone from the group.
        """
        group = self.get_object()

        if not self._user_can_manage_group(request.user, group):
            return Response(
                {"error": "You do not have permission to delete milestones."},
                status=status.HTTP_403_FORBIDDEN,
            )

        milestone = get_object_or_404(Milestone, pk=milestone_id, group=group)
        milestone.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        """
        Allow platform admins to delete a group.
        """

        if not IsPlatformAdmin().has_permission(request, self):
            return Response(
                {"error": "Only administrators can delete groups."},
                status=status.HTTP_403_FORBIDDEN,
            )

        group = self.get_object()
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        if not IsPlatformAdmin().has_permission(request, self):
            return Response(
                {"error": "Only administrators can create groups."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GroupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        group_id = validated.get("groupId") or self._generate_group_id()
        status_value = (validated.get("status") or "active").strip() or "active"
        mentor = None
        mentor_id = validated.get("mentorId")
        if mentor_id is not None:
            mentor = User.objects.get(pk=mentor_id)

        with transaction.atomic():
            group = Group.objects.create(
                id=group_id,
                name=validated["name"],
                track=validated.get("track", ""),
                status=status_value,
                mentor=mentor,
            )

            members_payload = validated.get("members", [])
            for member in members_payload:
                user = User.objects.get(pk=member["userId"])
                GroupMember.objects.create(
                    group=group,
                    user=user,
                    role=member.get("role") or "student",
                )

        group = (
            Group.objects.select_related("mentor")
            .prefetch_related("members__user", "milestones__tasks")
            .get(pk=group.pk)
        )
        output = GroupDetailSerializer(group)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _user_can_manage_group(user, group: Group) -> bool:
        if not user.is_authenticated:
            return False
        role = getattr(user, "role", "")
        if role in {"admin", "supervisor"} or user.is_staff:
            return True
        if group.mentor_id and group.mentor_id == user.id:
            return True
        return group.members.filter(user=user).exists()

    def _generate_group_id(self) -> str:
        base = "BTF"
        suffix = Group.objects.count() + 1
        while True:
            candidate = f"{base}{suffix:03d}"
            if not Group.objects.filter(pk=candidate).exists():
                return candidate
            suffix += 1
