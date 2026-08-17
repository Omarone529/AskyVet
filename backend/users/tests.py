from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User

PASSWORD = "UnaPasswordSicura!42"


def make_user(username, **extra):
    return User.objects.create_user(
        email=f"{username}@askyvet.it",
        username=username,
        password=PASSWORD,
        **extra,
    )


class AuthFlowTests(APITestCase):
    """The endpoints a frontend needs in order to sign anybody in at all."""

    def setUp(self):
        self.user = make_user("mario")

    def test_registration_creates_a_plain_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "nuovo@askyvet.it",
                "username": "nuovo",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username="nuovo")
        self.assertFalse(created.is_admin)
        self.assertFalse(created.is_staff)

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "nuovo@askyvet.it",
                "username": "nuovo",
                "password": PASSWORD,
                "password_confirm": "altro",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_cannot_grant_admin(self):
        """A self-registered user must not be able to elevate itself."""
        self.client.post(
            reverse("register"),
            {
                "email": "furbo@askyvet.it",
                "username": "furbo",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
                "is_admin": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        created = User.objects.get(username="furbo")
        self.assertFalse(created.is_admin)
        self.assertFalse(created.is_superuser)

    def test_login_returns_a_jwt_pair(self):
        """Regression: there was no login route at all, every path 404'd."""
        response = self.client.post(
            reverse("rest_login"),
            {"email": self.user.email, "password": PASSWORD},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejects_a_wrong_password(self):
        response = self.client.post(
            reverse("rest_login"),
            {"email": self.user.email, "password": "sbagliata"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_returns_a_new_access_token(self):
        login = self.client.post(
            reverse("rest_login"),
            {"email": self.user.email, "password": PASSWORD},
        )
        response = self.client.post(
            reverse("token_refresh"), {"refresh": login.data["refresh"]}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_banned_user_cannot_authenticate(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("rest_login"),
            {"email": self.user.email, "password": PASSWORD},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        self.assertEqual(
            self.client.get(reverse("me")).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_me_returns_the_current_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)


class AdminCreationTests(APITestCase):
    """An admin must be able to appoint another admin over the API."""

    def setUp(self):
        self.admin = make_user("capo", is_admin=True)
        self.regular = make_user("utente")

    def test_admin_can_create_another_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("admin-create"),
            {
                "email": "secondo@askyvet.it",
                "username": "secondo",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username="secondo")
        self.assertTrue(created.is_admin)
        # Also needs Django-admin access, or the new admin cannot reach /admin/.
        self.assertTrue(created.is_staff)

    def test_regular_user_cannot_create_an_admin(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            reverse("admin-create"),
            {
                "email": "secondo@askyvet.it",
                "username": "secondo",
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(username="secondo").exists())

    def test_anonymous_cannot_list_users(self):
        self.assertEqual(
            self.client.get(reverse("user-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)


class ModerationTests(APITestCase):
    """Ban and mute, including the cases a moderator must not be allowed."""

    def setUp(self):
        self.admin = make_user("moderatore", is_admin=True)
        self.other_admin = make_user("collega", is_admin=True)
        self.target = make_user("disturbatore")
        self.client.force_authenticate(user=self.admin)

    def ban_url(self, user):
        return reverse("ban-user", args=[user.id])

    def mute_url(self, user):
        return reverse("mute-user", args=[user.id])

    def test_admin_can_ban_a_user_with_a_reason(self):
        response = self.client.patch(
            self.ban_url(self.target), {"banned": True, "reason": "spam ripetuto"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.assertEqual(self.target.moderation_reason, "spam ripetuto")

    def test_ban_requires_a_reason(self):
        response = self.client.patch(self.ban_url(self.target), {"banned": True})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_ban_is_explicit_not_a_toggle(self):
        """Repeating the same call must be idempotent, not flip the state back."""
        payload = {"banned": True, "reason": "spam"}
        self.client.patch(self.ban_url(self.target), payload)
        self.client.patch(self.ban_url(self.target), payload)

        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_admin_can_reinstate_a_user(self):
        self.target.is_active = False
        self.target.save(update_fields=["is_active"])

        self.client.patch(self.ban_url(self.target), {"banned": False})

        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_admin_cannot_ban_another_admin(self):
        response = self.client.patch(
            self.ban_url(self.other_admin), {"banned": True, "reason": "x"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.other_admin.refresh_from_db()
        self.assertTrue(self.other_admin.is_active)

    def test_admin_cannot_ban_itself(self):
        response = self.client.patch(
            self.ban_url(self.admin), {"banned": True, "reason": "x"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_regular_user_cannot_ban_anyone(self):
        self.client.force_authenticate(user=self.target)
        victim = make_user("vittima")

        response = self.client.patch(
            self.ban_url(victim), {"banned": True, "reason": "x"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_mute_a_user_for_a_while(self):
        response = self.client.patch(
            self.mute_url(self.target), {"hours": 24, "reason": "toni aggressivi"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_muted)
        self.assertGreater(self.target.muted_until, timezone.now())

    def test_mute_can_be_lifted_with_zero_hours(self):
        self.target.muted_until = timezone.now() + timezone.timedelta(days=1)
        self.target.save(update_fields=["muted_until"])

        self.client.patch(self.mute_url(self.target), {"hours": 0})

        self.target.refresh_from_db()
        self.assertIsNone(self.target.muted_until)
        self.assertFalse(self.target.is_muted)

    def test_expired_mute_no_longer_counts(self):
        self.target.muted_until = timezone.now() - timezone.timedelta(hours=1)
        self.target.save(update_fields=["muted_until"])

        self.assertFalse(self.target.is_muted)
