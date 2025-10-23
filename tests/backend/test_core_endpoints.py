from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from .base import AuthenticatedAPITestCase


class CoreEndpointsTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_student("core@example.com")

    def test_health_check_reports_ok(self):
        url = reverse("core:health_check")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["status"], "healthy")
        self.assertIn("database", payload["services"])

    def test_health_check_handles_database_error(self):
        url = reverse("core:health_check")
        with patch("core.views.connection.cursor") as mock_cursor:
            mock_cursor.side_effect = Exception("db down")
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        payload = response.json()
        self.assertEqual(payload["status"], "unhealthy")

    def test_upload_file_requires_authentication(self):
        url = reverse("core:upload_file")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_file_succeeds(self):
        self.authenticate(self.user.user)
        url = reverse("core:upload_file")
        payload = {
            "file": SimpleUploadedFile(
                "notes.txt",
                BytesIO(b"sample-data").getvalue(),
                content_type="text/plain",
            )
        }

        with patch("core.views.default_storage") as storage:
            storage.save.return_value = "uploads/notes.txt"
            storage.url.return_value = "https://cdn.example.com/uploads/notes.txt"
            response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["filename"], "notes.txt")
