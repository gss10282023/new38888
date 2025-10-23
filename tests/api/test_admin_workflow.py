from django.urls import reverse
from rest_framework import status

from tests.backend.base import AuthenticatedAPITestCase


class AdminWorkflowTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.create_admin()
        self.student = self.create_student("workflow.student@example.com")
        self.authenticate(self.admin.user)

    def test_admin_dashboard_end_to_end(self):
        # Create another mentor for group creation
        mentor = self.create_user("workflow.mentor@example.com", role="mentor", status="active")

        # Create a group
        group_payload = {
            "groupId": "BTF150",
            "name": "Workflow Innovators",
            "track": "AUS-NSW",
            "status": "active",
            "mentorId": mentor.user.pk,
            "members": [{"userId": self.student.user.pk, "role": "student"}],
        }
        group_url = reverse("groups:group-list")
        group_response = self.client.post(group_url, group_payload, format="json")
        self.assertEqual(group_response.status_code, status.HTTP_201_CREATED)

        # Fetch stats and verify counts reflect the newly created data
        stats_url = reverse("admin_panel:stats")
        stats_response = self.client.get(stats_url)
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        stats = stats_response.json()
        self.assertGreaterEqual(stats["totalUsers"], 2)
        self.assertGreaterEqual(stats["activeGroups"], 1)

        # Fetch admin user list filtered by role
        user_list_url = reverse("admin_panel:user-list")
        list_response = self.client.get(user_list_url, {"role": "student"})
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(list_response.json()["count"], 1)

        # Update student status through status endpoint
        status_url = reverse(
            "admin_panel:user-update-status",
            kwargs={"pk": self.student.user.pk},
        )
        status_response = self.client.put(status_url, {"status": "inactive"}, format="json")
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.student.user.refresh_from_db()
        self.assertEqual(self.student.user.status, "inactive")
