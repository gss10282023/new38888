"""
Seed local demo data for BIOTech Futures Hub.

Runs safely multiple times (idempotent-ish): it uses get_or_create where possible
and updates key fields (roles/status) to keep the demo consistent.

Usage:
  # inside backend/ (recommended)
  python scripts/seed_demo_data.py

  # or via Django shell
  python manage.py shell < scripts/seed_demo_data.py
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Iterable


def setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "btf_backend.settings")
    import django  # noqa: WPS433
    from django.apps import apps  # noqa: WPS433

    if not apps.ready:
        django.setup()


def ensure_user(
    *,
    email: str,
    username: str | None = None,
    role: str,
    status: str = "active",
    password: str | None = None,
    unusable_password: bool = False,
    is_staff: bool = False,
    is_superuser: bool = False,
) -> "User":
    from django.contrib.auth import get_user_model  # noqa: WPS433

    User = get_user_model()
    normalized_email = (email or "").strip().lower()
    defaults = {"username": (username or normalized_email)[:150]}
    user, _created = User.objects.get_or_create(email=normalized_email, defaults=defaults)

    dirty = False
    if not user.username:
        user.username = defaults["username"]
        dirty = True

    if getattr(user, "role", None) != role:
        user.role = role
        dirty = True
    if getattr(user, "status", None) != status:
        user.status = status
        dirty = True

    if bool(user.is_staff) != bool(is_staff):
        user.is_staff = bool(is_staff)
        dirty = True
    if bool(user.is_superuser) != bool(is_superuser):
        user.is_superuser = bool(is_superuser)
        dirty = True

    if password:
        user.set_password(password)
        dirty = True
    elif unusable_password and user.has_usable_password():
        user.set_unusable_password()
        dirty = True

    if dirty:
        user.save()

    from users.models import UserProfile  # noqa: WPS433

    UserProfile.objects.get_or_create(user=user)
    return user


def ensure_group_members(group: "Group", *, members: Iterable[tuple["User", str]]) -> None:
    from groups.models import GroupMember  # noqa: WPS433

    for user, role in members:
        GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={"role": role},
        )


def main() -> None:
    setup_django()

    from announcements.models import Announcement  # noqa: WPS433
    from chat.models import Message  # noqa: WPS433
    from events.models import Event, EventRegistration  # noqa: WPS433
    from groups.models import Group, Milestone, Task  # noqa: WPS433
    from resources.models import Resource  # noqa: WPS433

    admin_email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@demo.local")
    admin_username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
    admin_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin123456")

    admin_user = ensure_user(
        email=admin_email,
        username=admin_username,
        role="admin",
        status="active",
        password=admin_password,
        is_staff=True,
        is_superuser=True,
    )
    mentor_user = ensure_user(
        email=os.getenv("DEMO_MENTOR_EMAIL", "mentor@demo.local"),
        role="mentor",
        status="active",
        unusable_password=True,
    )
    student_user = ensure_user(
        email=os.getenv("DEMO_STUDENT_EMAIL", "student@demo.local"),
        role="student",
        status="active",
        unusable_password=True,
    )
    supervisor_user = ensure_user(
        email=os.getenv("DEMO_SUPERVISOR_EMAIL", "supervisor@demo.local"),
        role="supervisor",
        status="active",
        unusable_password=True,
    )

    group_id = os.getenv("DEMO_GROUP_ID", "BTF001")
    group, _ = Group.objects.get_or_create(
        id=group_id,
        defaults={
            "name": os.getenv("DEMO_GROUP_NAME", "Demo Group"),
            "track": os.getenv("DEMO_GROUP_TRACK", "Global"),
            "status": "active",
            "mentor": mentor_user,
        },
    )
    if group.mentor_id != mentor_user.id:
        group.mentor = mentor_user
        group.save(update_fields=["mentor"])

    ensure_group_members(
        group,
        members=[
            (mentor_user, "mentor"),
            (student_user, "student"),
            (supervisor_user, "supervisor"),
        ],
    )

    milestones_payload = [
        (
            "Ideation",
            "Define the problem and validate assumptions.",
            [
                ("Draft your problem statement", False, student_user),
                ("Interview 3 potential users", True, student_user),
            ],
        ),
        (
            "Prototype",
            "Build a lightweight prototype and iterate quickly.",
            [
                ("Create a clickable UI prototype", False, student_user),
                ("Get mentor feedback", False, mentor_user),
            ],
        ),
        (
            "Pitch",
            "Prepare the final narrative and demo.",
            [
                ("Write a 5-slide pitch deck", False, student_user),
                ("Record a 30s demo video", False, student_user),
            ],
        ),
    ]

    for index, (title, description, tasks) in enumerate(milestones_payload, start=1):
        milestone, _ = Milestone.objects.get_or_create(
            group=group,
            title=title,
            defaults={
                "description": description,
                "order_index": index,
            },
        )
        updated_fields: list[str] = []
        if milestone.order_index != index:
            milestone.order_index = index
            updated_fields.append("order_index")
        if description and milestone.description != description:
            milestone.description = description
            updated_fields.append("description")
        if updated_fields:
            milestone.save(update_fields=updated_fields)

        for task_name, completed, assigned_to in tasks:
            task, _ = Task.objects.get_or_create(
                milestone=milestone,
                name=task_name,
                defaults={
                    "completed": bool(completed),
                    "assigned_to": assigned_to,
                },
            )
            task_updates: list[str] = []
            if task.completed != bool(completed):
                task.completed = bool(completed)
                task_updates.append("completed")
            if assigned_to and task.assigned_to_id != assigned_to.id:
                task.assigned_to = assigned_to
                task_updates.append("assigned_to")
            if task_updates:
                task.save(update_fields=task_updates)

    if not Message.objects.filter(group=group).exists():
        Message.objects.create(
            group=group,
            author=mentor_user,
            text="Welcome to the demo group! Share your weekly progress here.",
        )
        Message.objects.create(
            group=group,
            author=student_user,
            text="Got it — starting with the problem statement and interviews.",
        )

    Announcement.objects.get_or_create(
        title="Welcome to BIOTech Futures Hub",
        defaults={
            "summary": "This is seeded demo content for local development.",
            "content": "Use Docker Compose to start the full stack and explore the UI.",
            "author": "Program Team",
            "audience": "all",
        },
    )
    Announcement.objects.get_or_create(
        title="Mentor Office Hours",
        defaults={
            "summary": "Weekly drop-in session for Q&A.",
            "content": "Bring questions about milestones, experiments, and pitching.",
            "author": "Program Team",
            "audience": "student",
            "link": "https://example.org/events/office-hours",
        },
    )

    Resource.objects.get_or_create(
        title="Milestone Template (Demo)",
        defaults={
            "description": "Sample milestone template for the demo environment.",
            "type": "template",
            "role": "all",
            "file_url": "https://example.org/resources/milestone-template.pdf",
            "cover_image": "https://picsum.photos/seed/btf-template/800/450",
        },
    )
    Resource.objects.get_or_create(
        title="Pitch Deck Guide (Demo)",
        defaults={
            "description": "How to craft a clear, compelling pitch in 5 slides.",
            "type": "guide",
            "role": "student",
            "file_url": "https://example.org/resources/pitch-deck-guide.pdf",
            "cover_image": "https://picsum.photos/seed/btf-guide/800/450",
        },
    )

    today = date.today()
    kickoff, _ = Event.objects.get_or_create(
        title="Demo Kickoff Workshop",
        defaults={
            "description": "Quick overview of the program and expectations.",
            "long_description": "This seeded event exists for local demo purposes.",
            "date": today + timedelta(days=3),
            "time": "17:00",
            "location": "Online",
            "type": "virtual",
            "cover_image": "https://picsum.photos/seed/btf-event/1200/675",
            "register_link": "https://example.org/register",
            "capacity": 200,
        },
    )
    EventRegistration.objects.get_or_create(event=kickoff, user=student_user)

    print("[seed] Demo data is ready.")
    print(f"[seed] Admin: {admin_user.email} (password: {admin_password})")
    print("[seed] Other accounts use OTP login (see backend logs for the 6-digit code).")


if __name__ == "__main__":
    main()

