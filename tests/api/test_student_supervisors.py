from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import StudentSupervisor, User


class StudentSupervisorRelationshipTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user(
            email="admin@example.com",
            username="admin@example.com",
            password="adminpass",
            role="admin",
            status="active",
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            username="student@example.com",
            password="studentpass",
            role="student",
            status="active",
        )
        self.supervisor = User.objects.create_user(
            email="supervisor@example.com",
            username="supervisor@example.com",
            password="supervisorpass",
            role="supervisor",
            status="active",
        )

    def test_admin_can_create_relationship(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("admin_panel:student-supervisors-list")
        payload = {
            "studentId": self.student.id,
            "supervisorId": self.supervisor.id,
            "relationshipType": StudentSupervisor.RELATIONSHIP_GUARDIAN,
            "joinPermissionGranted": True,
            "notes": "Guardian approval received 2025-02-01",
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data["student"]["id"], self.student.id)
        self.assertEqual(data["supervisor"]["id"], self.supervisor.id)
        self.assertEqual(data["relationshipType"], "guardian")
        self.assertTrue(data["joinPermissionGranted"])
        self.assertEqual(
            data["notes"],
            "Guardian approval received 2025-02-01",
        )

        self.assertEqual(StudentSupervisor.objects.count(), 1)
        relationship = StudentSupervisor.objects.first()
        self.assertTrue(relationship.join_permission_granted)
        self.assertIsNotNone(relationship.join_permission_granted_at)

    def test_participants_can_toggle_join_permission(self):
        relationship = StudentSupervisor.objects.create(
            student=self.student,
            supervisor=self.supervisor,
            relationship_type=StudentSupervisor.RELATIONSHIP_SUPERVISOR,
        )

        # Student lists current relationships.
        self.client.force_authenticate(user=self.student)
        list_url = reverse("users:me-supervisors")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertFalse(payload["results"][0]["joinPermissionGranted"])

        # Student grants permission.
        detail_url = reverse("users:me-supervisor-detail", args=[relationship.pk])
        response = self.client.patch(
            detail_url,
            {"joinPermissionGranted": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["joinPermissionGranted"])

        relationship.refresh_from_db()
        self.assertTrue(relationship.join_permission_granted)
        self.assertIsNotNone(relationship.join_permission_granted_at)

