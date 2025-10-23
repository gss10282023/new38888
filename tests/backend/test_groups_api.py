from django.urls import reverse
from rest_framework import status

from groups.models import Group, Milestone, Task

from .base import AuthenticatedAPITestCase


class GroupEndpointsTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.create_admin()
        self.student = self.create_student("student@example.com")
        self.mentor = self.create_user("mentor@example.com", role="mentor", status="active")

        self.group = self.create_group(
            group_id="BTF002",
            name="Genome Explorers",
            mentor=self.mentor.user,
            members=[self.student.user],
        )
        self.milestone = self.add_milestone(self.group, title="Kick-off")
        self.task = self.add_task(self.milestone, name="Submit proposal", completed=False)

    def test_list_groups_respects_role_visibility(self):
        url = reverse("groups:group-list")
        self.authenticate(self.student.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload["groups"]), 1)

        # Admins see all groups regardless of membership
        self.authenticate(self.admin.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertGreaterEqual(len(payload["groups"]), 1)

    def test_my_groups_endpoint_returns_memberships(self):
        url = reverse("groups:group-my-groups")
        self.authenticate(self.student.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload["groups"]), 1)
        self.assertEqual(payload["groups"][0]["id"], self.group.id)

    def test_retrieve_group_returns_members_and_milestones(self):
        url = reverse("groups:group-detail", kwargs={"pk": self.group.pk})
        self.authenticate(self.student.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["name"], "Genome Explorers")
        self.assertEqual(len(body["members"]), 1)
        self.assertEqual(len(body["milestones"]), 1)

    def test_add_task_to_milestone(self):
        url = reverse(
            "groups:group-add-task",
            kwargs={"pk": self.group.pk, "milestone_id": self.milestone.pk},
        )
        self.authenticate(self.mentor.user)
        response = self.client.post(url, {"name": "Prepare slides"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Task.objects.filter(milestone=self.milestone, name="Prepare slides").exists()
        )

    def test_update_task_completion(self):
        url = reverse(
            "groups:group-update-task",
            kwargs={"pk": self.group.pk, "task_id": self.task.pk},
        )
        self.authenticate(self.student.user)
        response = self.client.put(url, {"completed": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_create_and_delete_milestone_requires_privileges(self):
        create_url = reverse("groups:group-create-milestone", kwargs={"pk": self.group.pk})

        # Student can create milestone because they are a member
        self.authenticate(self.student.user)
        response = self.client.post(
            create_url,
            {"title": "Prototype", "description": "Build initial prototype"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_id = response.json()["id"]

        delete_url = reverse(
            "groups:group-delete-milestone",
            kwargs={"pk": self.group.pk, "milestone_id": new_id},
        )
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Milestone.objects.filter(pk=new_id).exists())

    def test_create_group_requires_admin(self):
        url = reverse("groups:group-list")
        payload = {
            "groupId": "BTF100",
            "name": "Cell Builders",
            "track": "Global",
            "status": "active",
            "mentorId": self.mentor.user.pk,
            "members": [{"userId": self.student.user.pk, "role": "student"}],
        }

        # Non-admin rejected
        self.authenticate(self.student.user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin succeeds
        self.authenticate(self.admin.user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Group.objects.filter(pk="BTF100").exists())

    def test_delete_group_requires_admin(self):
        url = reverse("groups:group-detail", kwargs={"pk": self.group.pk})

        self.authenticate(self.student.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.admin.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(pk=self.group.pk).exists())

    def test_access_denied_for_non_members(self):
        outsider = self.create_student("outsider@example.com")
        self.authenticate(outsider.user)

        detail_url = reverse("groups:group-detail", kwargs={"pk": self.group.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
