from django.urls import reverse
from rest_framework import status

from announcements.models import Announcement

from .base import AuthenticatedAPITestCase


class AnnouncementEndpointsTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.create_admin()
        self.student = self.create_student("student@hub.com")
        self.mentor = self.create_user("mentor@hub.com", role="mentor", status="active")

        Announcement.objects.create(
            title="Welcome!",
            summary="Program kickoff",
            content="Join the opening ceremony.",
            author="Program Team",
            audience=Announcement.AUDIENCE_ALL,
        )
        Announcement.objects.create(
            title="Mentor Briefing",
            summary="Mentor-only session",
            content="Details for mentors.",
            author="Admin",
            audience=Announcement.AUDIENCE_MENTOR,
        )

    def test_list_announcements_filters_by_role(self):
        url = reverse("announcements:announcement-list")

        self.authenticate(self.student.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["count"], 1)

        self.authenticate(self.mentor.user)
        response = self.client.get(url)
        self.assertEqual(response.json()["count"], 2)

    def test_create_and_delete_requires_admin(self):
        url = reverse("announcements:announcement-list")
        payload = {
            "title": "Update",
            "summary": "Important change",
            "content": "Content for everyone",
            "author": "Admin",
            "audience": Announcement.AUDIENCE_ALL,
        }

        self.authenticate(self.student.user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.admin.user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        announcement_id = response.json()["id"]

        delete_url = reverse("announcements:announcement-detail", kwargs={"pk": announcement_id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

