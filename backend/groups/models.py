from django.conf import settings
from django.db import models


class Group(models.Model):
    """
    Represents a competition group consisting of mentors and students.
    Uses a short string identifier such as BTF046 as the primary key.
    """

    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    track = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, default="active")
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mentored_groups",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name or self.id


class GroupMember(models.Model):
    """
    Associates a user with a group, storing their role within the team.
    """

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    role = models.CharField(max_length=20)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")
        ordering = ["joined_at"]

    def __str__(self) -> str:
        return f"{self.user} in {self.group} ({self.role})"


class Milestone(models.Model):
    """
    Represents a milestone within a group, grouping several tasks together.
    """

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_index = models.IntegerField(default=0)

    class Meta:
        ordering = ["order_index", "id"]

    def __str__(self) -> str:
        return f"{self.group_id} - {self.title}"


class Task(models.Model):
    """
    Individual task under a milestone. Can be assigned to a specific user.
    """

    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    name = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return self.name
