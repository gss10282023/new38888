from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from announcements.models import Announcement
from events.models import Event
from resources.models import Resource

from tests.backend.base import AuthenticatedAPITestCase


class ContentAccessFlowTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.create_admin("content.admin@example.com")
        self.mentor = self.create_user("content.mentor@example.com", role="mentor", status="active")
        self.student = self.create_student("content.student@example.com")

        # Seed content
        Resource.objects.create(
            title="General Guide",
            description="For everyone",
            type=Resource.TYPE_GUIDE,
            role=Resource.ROLE_ALL,
            file_url="https://cdn.example.com/files/general.pdf",
        )
        Resource.objects.create(
            title="Mentor Handbook",
            description="Restricted resource",
            type=Resource.TYPE_GUIDE,
            role=Resource.ROLE_MENTOR,
            file_url="https://cdn.example.com/files/mentor.pdf",
        )
        Event.objects.create(
            title="Networking Night",
            description="In-person meetup",
            long_description="Agenda",
            date=date.today() + timedelta(days=5),
            time="18:00",
            location="Sydney",
            type=Event.TYPE_IN_PERSON,
        )
        Announcement.objects.create(
            title="Global Update",
            summary="Applies to all",
            content="Hello everyone!",
            audience=Announcement.AUDIENCE_ALL,
        )
        Announcement.objects.create(
            title="Mentor Update",
            summary="Mentor-specific",
            content="Mentor details",
            audience=Announcement.AUDIENCE_MENTOR,
        )

        self.mentor_client = APIClient()
        self.mentor_client.force_authenticate(user=self.mentor.user)
        self.student_client = APIClient()
        self.student_client.force_authenticate(user=self.student.user)

    def test_students_and_mentors_access_content(self):
        resource_url = reverse("resources:resource-list")
        student_resources = self.student_client.get(resource_url).json()
        mentor_resources = self.mentor_client.get(resource_url).json()
        self.assertEqual(student_resources["count"], 1)
        self.assertEqual(mentor_resources["count"], 2)

        events_url = reverse("events:event-list")
        self.assertEqual(self.student_client.get(events_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.mentor_client.get(events_url).json()["count"], 1)

        announcements_url = reverse("announcements:announcement-list")
        student_announcements = self.student_client.get(announcements_url).json()
        mentor_announcements = self.mentor_client.get(announcements_url).json()
        self.assertEqual(student_announcements["count"], 1)
        self.assertEqual(mentor_announcements["count"], 2)

