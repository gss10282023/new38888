from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from groups.models import Group

from .models import Message, MessageAttachment
from .serializers import MessageSerializer


class MessageViewSet(viewsets.ViewSet):
    """
    Provides listing and creation of chat messages scoped to a group.
    """

    permission_classes = [IsAuthenticated]
    max_page_size = 100
    default_page_size = 50

    def list(self, request, group_id: str) -> Response:
        group = self._get_group_or_403(group_id, request.user)
        queryset = (
            Message.objects.filter(group=group)
            .select_related("author")
            .prefetch_related("attachments")
            .order_by("-created_at", "-id")
        )

        before_param = request.query_params.get("before")
        if before_param:
            before_dt = parse_datetime(before_param)
            if before_dt is None:
                raise ValidationError({"before": "Invalid datetime format."})
            if timezone.is_naive(before_dt):
                before_dt = timezone.make_aware(before_dt, timezone=timezone.utc)
            queryset = queryset.filter(created_at__lt=before_dt)

        limit = request.query_params.get("limit")
        try:
            page_size = int(limit) if limit is not None else self.default_page_size
        except (TypeError, ValueError):
            raise ValidationError({"limit": "Limit must be an integer."})
        page_size = max(1, min(page_size, self.max_page_size))

        messages = list(queryset[: page_size + 1])
        has_more = len(messages) > page_size
        messages = messages[:page_size]

        serializer = MessageSerializer(messages, many=True)
        return Response(
            {
                "messages": serializer.data,
                "hasMore": has_more,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, group_id: str) -> Response:
        group = self._get_group_or_403(group_id, request.user)

        text = (request.data.get("text") or "").strip()
        attachments_payload = request.data.get("attachments") or []

        if not text and not attachments_payload:
            raise ValidationError("Message text or attachments are required.")

        message = Message.objects.create(
            group=group,
            author=request.user,
            text=text,
        )

        attachments_to_create: list[MessageAttachment] = []
        for item in attachments_payload:
            if not isinstance(item, dict):
                raise ValidationError({"attachments": "Each attachment must be an object."})

            file_url = item.get("url") or item.get("file_url")
            filename = item.get("filename")
            file_size = item.get("size") or item.get("file_size")
            mime_type = item.get("mimeType") or item.get("mime_type") or ""

            if not file_url:
                raise ValidationError({"attachments": "Attachment is missing url."})
            if not filename:
                raise ValidationError({"attachments": "Attachment is missing filename."})

            try:
                file_size_value = int(file_size) if file_size is not None else 0
            except (TypeError, ValueError):
                raise ValidationError({"attachments": "Attachment size must be an integer."})

            attachments_to_create.append(
                MessageAttachment(
                    message=message,
                    file_url=file_url,
                    filename=filename,
                    file_size=file_size_value,
                    mime_type=mime_type or "application/octet-stream",
                )
            )

        if attachments_to_create:
            MessageAttachment.objects.bulk_create(attachments_to_create)

        message = (
            Message.objects.select_related("author")
            .prefetch_related("attachments")
            .get(pk=message.pk)
        )
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _get_group_or_403(self, group_id: str, user) -> Group:
        group = get_object_or_404(Group.objects.select_related("mentor"), pk=group_id)
        if not self._user_has_access(user, group):
            raise PermissionDenied("You do not have access to this group.")
        return group

    @staticmethod
    def _user_has_access(user, group: Group) -> bool:
        if not user.is_authenticated:
            return False

        if getattr(user, "role", None) in {"admin", "supervisor"} or user.is_staff:
            return True

        if group.mentor_id == user.id:
            return True

        return group.members.filter(user=user).exists()
