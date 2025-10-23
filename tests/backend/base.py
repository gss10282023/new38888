"""
Shared utilities for backend API tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from groups.models import Group, GroupMember, Milestone, Task
from users.models import UserProfile

User = get_user_model()


@dataclass
class TestUser:
    user: User
    password: str


class AuthenticatedAPITestCase(APITestCase):
    """
    Base class that offers helper builders for quickly setting up users,
    groups, and authenticated API clients.
    """

    def create_user(
        self,
        email: str,
        *,
        role: str = "student",
        status: str = "active",
        track: str = "Global",
        is_staff: bool = False,
        is_superuser: bool = False,
        password: Optional[str] = None,
    ) -> TestUser:
        password = password or "Passw0rd!"
        user = User.objects.create_user(
            email=email.lower(),
            username=email.lower(),
            password=password,
        )
        user.role = role
        user.status = status
        user.track = track
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()

        UserProfile.objects.get_or_create(user=user)

        return TestUser(user=user, password=password)

    def create_admin(self, email: str = "admin@example.com") -> TestUser:
        return self.create_user(
            email,
            role="admin",
            status="active",
            track="Global",
            is_staff=True,
        )

    def create_student(self, email: str, *, track: str = "AUS-NSW") -> TestUser:
        return self.create_user(email, role="student", status="active", track=track)

    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def create_group(
        self,
        *,
        group_id: str = "BTF100",
        name: str = "BioTech Pioneers",
        mentor: Optional[User] = None,
        members: Optional[Iterable[User]] = None,
        track: str = "AUS-NSW",
        status: str = "active",
    ) -> Group:
        group = Group.objects.create(
            id=group_id,
            name=name,
            mentor=mentor,
            track=track,
            status=status,
        )
        for member in members or []:
            GroupMember.objects.create(group=group, user=member, role="student")
        return group

    def add_milestone(
        self,
        group: Group,
        *,
        title: str = "Design Sprint",
        description: str = "Define problem statements",
        order_index: int = 1,
    ) -> Milestone:
        return group.milestones.create(
            title=title,
            description=description,
            order_index=order_index,
        )

    def add_task(
        self,
        milestone: Milestone,
        *,
        name: str = "Submit brief",
        completed: bool = False,
        assigned_to: Optional[User] = None,
    ) -> Task:
        return milestone.tasks.create(
            name=name,
            completed=completed,
            assigned_to=assigned_to,
        )

    @staticmethod
    def reverse(path_name: str, **kwargs):
        return reverse(path_name, kwargs=kwargs or None)

