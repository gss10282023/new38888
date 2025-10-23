from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from groups.models import Group, GroupMember, Milestone, Task
from users.models import User


class GroupAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com",
            username="student@example.com",
            password="testpass123",
            first_name="Student",
            last_name="User",
        )
        self.mentor = User.objects.create_user(
            email="mentor@example.com",
            username="mentor@example.com",
            password="testpass123",
            first_name="Mentor",
            last_name="User",
            role="mentor",
        )
        self.group = Group.objects.create(
            id="BTF046",
            name="BTF046",
            track="AUS-NSW",
            status="Schedule Event",
            mentor=self.mentor,
        )
        GroupMember.objects.create(
            group=self.group,
            user=self.user,
            role="student",
        )
        self.milestone = Milestone.objects.create(
            group=self.group,
            title="Getting Started",
        )
        self.task = Task.objects.create(
            milestone=self.milestone,
            name="Determine Group Topic",
        )

        self.client.force_authenticate(user=self.user)

    def test_get_my_groups_returns_user_groups(self):
        url = reverse("groups:group-my-groups")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("groups", response.data)
        self.assertEqual(len(response.data["groups"]), 1)
        group_payload = response.data["groups"][0]
        self.assertEqual(group_payload["id"], self.group.id)
        self.assertEqual(group_payload["members"], 1)
        self.assertEqual(group_payload["mentor"]["id"], self.mentor.id)
        self.assertEqual(group_payload["mentor"]["name"], "Mentor User")

    def test_get_group_detail_includes_members_and_milestones(self):
        url = reverse("groups:group-detail", kwargs={"pk": self.group.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.group.id)
        self.assertEqual(response.data["name"], self.group.name)
        self.assertEqual(len(response.data["members"]), 1)
        self.assertEqual(response.data["members"][0]["id"], self.user.id)
        self.assertEqual(response.data["members"][0]["role"], "student")
        self.assertEqual(len(response.data["milestones"]), 1)
        milestone_payload = response.data["milestones"][0]
        self.assertEqual(milestone_payload["title"], "Getting Started")
        self.assertEqual(len(milestone_payload["tasks"]), 1)
        self.assertEqual(
            milestone_payload["tasks"][0]["name"],
            "Determine Group Topic",
        )

    def test_add_task_creates_task_under_milestone(self):
        url = reverse(
            "groups:group-add-task",
            kwargs={
                "pk": self.group.id,
                "milestone_id": self.milestone.id,
            },
        )
        response = self.client.post(
            url,
            {"name": "Submit team charter"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Submit team charter")
        self.assertFalse(response.data["completed"])
        self.assertTrue(
            self.milestone.tasks.filter(name="Submit team charter").exists()
        )

    def test_add_task_rejects_blank_name(self):
        url = reverse(
            "groups:group-add-task",
            kwargs={
                "pk": self.group.id,
                "milestone_id": self.milestone.id,
            },
        )
        response = self.client.post(url, {"name": "   "}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_task_marks_completed(self):
        url = reverse(
            "groups:group-update-task",
            kwargs={
                "pk": self.group.id,
                "task_id": self.task.id,
            },
        )
        response = self.client.put(url, {"completed": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)
        self.assertTrue(response.data["task"]["completed"])

    def test_create_milestone(self):
        url = reverse("groups:group-create-milestone", kwargs={"pk": self.group.id})
        response = self.client.post(
            url,
            {"title": "Prototype", "description": "Build initial prototype"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Prototype")
        self.assertEqual(response.data["description"], "Build initial prototype")
        self.assertTrue(
            Milestone.objects.filter(group=self.group, title="Prototype").exists()
        )

    def test_delete_milestone(self):
        milestone = Milestone.objects.create(group=self.group, title="To Remove")
        url = reverse(
            "groups:group-delete-milestone",
            kwargs={"pk": self.group.id, "milestone_id": milestone.id},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Milestone.objects.filter(group=self.group, title="To Remove").exists()
        )
