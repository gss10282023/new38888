import csv
from io import StringIO

from django.urls import reverse
from rest_framework import status

from groups.models import Group
from .base import AuthenticatedAPITestCase


class CurrentUserEndpointTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.account = self.create_student("member@example.com", track="AUS-NSW")
        self.authenticate(self.account.user)

    def test_get_current_user_returns_profile(self):
        url = reverse("users:me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["email"], self.account.user.email)
        self.assertEqual(payload["track"], "AUS-NSW")
        self.assertIn("profile", payload)
        self.assertEqual(payload["profile"]["country"], "")

    def test_update_current_user_updates_profile_and_track(self):
        url = reverse("users:me")
        response = self.client.put(
            url,
            {
                "track": "Global",
                "profile": {
                    "firstName": "Ada",
                    "lastName": "Lovelace",
                    "areasOfInterest": ["AI", "Synthetic Biology"],
                    "availability": "Weekends",
                    "yearLevel": 11,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["track"], "Global")
        self.assertEqual(payload["profile"]["firstName"], "Ada")
        self.assertEqual(payload["profile"]["areasOfInterest"], ["AI", "Synthetic Biology"])
        self.account.user.refresh_from_db()
        self.assertEqual(self.account.user.first_name, "Ada")
        self.assertEqual(self.account.user.profile.year_level, 11)

    def test_update_current_user_rejects_non_object_profile(self):
        url = reverse("users:me")
        response = self.client.patch(url, {"profile": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())


class AdminEndpointsTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.create_admin()
        self.authenticate(self.admin.user)

    def _seed_users(self):
        students = [
            self.create_student("student1@example.com", track="AUS-NSW"),
            self.create_student("student2@example.com", track="Global"),
        ]
        mentor = self.create_user("mentor@example.com", role="mentor", status="active")
        supervisor = self.create_user("supervisor@example.com", role="supervisor", status="active")

        group = self.create_group(
            group_id="BTF001",
            mentor=mentor.user,
            members=[member.user for member in students],
        )
        return students, mentor, supervisor, group

    def test_admin_stats_aggregates_counts(self):
        students, mentor, supervisor, group = self._seed_users()
        Group.objects.filter(pk=group.pk).update(status="active")

        url = reverse("admin_panel:stats")
        response = self.client.get(url, {"track": "Global"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["activeGroups"], 1)
        self.assertEqual(payload["mentors"]["total"], 1)
        self.assertEqual(payload["students"]["pending"], 0)

    def test_admin_user_list_supports_filters_and_pagination(self):
        self._seed_users()

        url = reverse("admin_panel:user-list")
        response = self.client.get(url, {"role": "student", "page_size": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["results"]), 1)

    def test_admin_user_creation_and_update_flow(self):
        create_url = reverse("admin_panel:user-list")
        payload = {
            "email": "new.user@example.com",
            "role": "mentor",
            "status": "active",
            "track": "AUS-NSW",
            "profile": {
                "firstName": "New",
                "lastName": "Mentor",
                "areasOfInterest": ["Robotics"],
            },
        }
        create_response = self.client.post(create_url, payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        user_id = create_response.json()["id"]

        detail_url = reverse("admin_panel:user-detail", kwargs={"pk": user_id})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.json()["email"], payload["email"])

        update_payload = {
            "email": "updated.user@example.com",
            "role": "mentor",
            "status": "inactive",
            "track": "Global",
        }
        update_response = self.client.put(detail_url, update_payload, format="json")
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        body = update_response.json()
        self.assertEqual(body["status"], "inactive")
        self.assertEqual(body["track"], "Global")
        self.assertEqual(body["email"], "updated.user@example.com")

    def test_admin_user_status_endpoint(self):
        target = self.create_student("status@example.com")

        url = reverse("admin_panel:user-update-status", kwargs={"pk": target.user.pk})
        response = self.client.put(url, {"status": "inactive"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target.user.refresh_from_db()
        self.assertEqual(target.user.status, "inactive")

    def test_admin_user_filters_endpoint_returns_metadata(self):
        self.create_student("filter@example.com", track="AUS-QLD")

        url = reverse("admin_panel:user-filters")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("tracks", payload)
        self.assertIn("roles", payload)
        self.assertIn("statuses", payload)

    def test_admin_user_export_returns_csv(self):
        self.create_student("export@example.com", track="AUS-NSW")

        url = reverse("admin_panel:user-export")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content_disposition = response["Content-Disposition"]
        self.assertIn("users-export-", content_disposition)

        rows = list(csv.reader(StringIO(response.content.decode("utf-8"))))
        self.assertGreaterEqual(len(rows), 2)  # header + at least one row

    def test_admin_cannot_delete_self_or_superuser(self):
        me_url = reverse("admin_panel:user-detail", kwargs={"pk": self.admin.user.pk})
        response = self.client.delete(me_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        superuser = self.create_user(
            "root@example.com",
            role="admin",
            status="active",
            is_superuser=True,
            is_staff=True,
        )
        superuser_url = reverse("admin_panel:user-detail", kwargs={"pk": superuser.user.pk})
        response = self.client.delete(superuser_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_forbidden_from_admin_routes(self):
        self.client.force_authenticate(user=None)
        student = self.create_student("forbidden@example.com")
        self.authenticate(student.user)

        url = reverse("admin_panel:user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
