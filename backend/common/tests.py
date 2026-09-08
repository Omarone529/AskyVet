from django.test import SimpleTestCase
from django.urls import reverse


class HealthzTests(SimpleTestCase):
    """
    The endpoint the frontend pings to wake the sleeping web service.

    ``SimpleTestCase`` on purpose: it forbids database access outright, so the
    day someone adds a query to the view these tests fail. A ping that waits on
    the database would give back part of the cold start it exists to hide.
    """

    def test_answers_ok(self):
        response = self.client.get(reverse("healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})

    def test_is_not_cached(self):
        """A cached answer would leave the container asleep."""
        response = self.client.get(reverse("healthz"))

        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_url_has_no_trailing_slash(self):
        """
        APPEND_SLASH would turn every ping into a redirect, and the ping is
        fired on each page load.
        """
        self.assertEqual(reverse("healthz"), "/healthz")
