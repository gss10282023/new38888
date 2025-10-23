from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from PIL import Image

from resources.models import Resource

from .base import AuthenticatedAPITestCase


def build_png_file(name: str = "cover.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color="white").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

class ResourceEndpointsTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.create_admin()
        self.student = self.create_student("library@example.com", track="AUS-NSW")

        self.resource = Resource.objects.create(
            title="Design Brief Template",
            description="Template for project proposals",
            type=Resource.TYPE_TEMPLATE,
            role=Resource.ROLE_ALL,
            file_url="https://cdn.example.com/files/template.docx",
        )

    def test_list_resources_filters_by_role(self):
        url = reverse("resources:resource-list")

        self.authenticate(self.student.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["count"], 1)

        # Create mentor only resource
        Resource.objects.create(
            title="Mentor Guide",
            description="For mentors only",
            type=Resource.TYPE_GUIDE,
            role=Resource.ROLE_MENTOR,
            file_url="https://cdn.example.com/files/guide.pdf",
        )

        response = self.client.get(url)
        self.assertEqual(response.json()["count"], 1)

        mentor = self.create_user("mentor@example.com", role="mentor", status="active")
        self.authenticate(mentor.user)
        response = self.client.get(url)
        self.assertEqual(response.json()["count"], 2)

    def test_create_resource_requires_admin(self):
        url = reverse("resources:resource-list")
        student_payload = {
            "title": "Lab Safety Checklist",
            "description": "Keep labs safe",
            "type": Resource.TYPE_GUIDE,
            "role": Resource.ROLE_ALL,
            "file": SimpleUploadedFile("safety.pdf", b"content", content_type="application/pdf"),
        }

        self.authenticate(self.student.user)
        response = self.client.post(url, student_payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        admin_payload = {
            "title": "Lab Safety Checklist",
            "description": "Keep labs safe",
            "type": Resource.TYPE_GUIDE,
            "role": Resource.ROLE_ALL,
            "file": SimpleUploadedFile("safety.pdf", b"content", content_type="application/pdf"),
        }

        self.authenticate(self.admin.user)
        with patch("resources.views.default_storage") as storage:
            storage.save.return_value = "resources/files/safety.pdf"
            storage.url.return_value = "https://cdn.example.com/resources/files/safety.pdf"

            response = self.client.post(url, admin_payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["title"], "Lab Safety Checklist")
        self.assertTrue(body["url"].endswith("safety.pdf"))

    def test_update_resource_cover(self):
        url = reverse("resources:resource-update-cover", kwargs={"pk": self.resource.pk})
        payload = {"coverImage": build_png_file()}

        self.authenticate(self.admin.user)
        with patch("resources.views.default_storage") as storage:
            storage.save.return_value = "resources/covers/cover.png"
            storage.url.return_value = "https://cdn.example.com/resources/covers/cover.png"
            response = self.client.put(url, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.resource.refresh_from_db()
        self.assertTrue(self.resource.cover_image.endswith("cover.png"))

    def test_delete_resource_requires_admin(self):
        url = reverse("resources:resource-detail", kwargs={"pk": self.resource.pk})

        self.authenticate(self.student.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.admin.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Resource.objects.filter(pk=self.resource.pk).exists())
