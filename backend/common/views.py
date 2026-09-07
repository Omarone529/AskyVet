"""Views that belong to no single app."""

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request):
    """
    Cheap liveness endpoint, used to wake the service up.

    On Render's free tier the web service is suspended after ~15 minutes of
    inactivity, and the first request that arrives afterwards pays a 30-60s
    cold start. The frontend pings this endpoint the moment the page starts
    loading, so the container is already booting while the browser is still
    downloading the JavaScript bundle (see the wake-on-entry snippet in
    frontend/index.html).

    It has to stay as cheap as it looks: no database query, no authentication,
    no serializer. Waking the container up is the whole point -- what the
    answer contains does not matter, only that it arrives.
    """
    response = JsonResponse({"status": "ok"})
    # A proxy or the browser cache answering on our behalf would defeat the
    # ping: the request would never reach the sleeping container.
    response["Cache-Control"] = "no-store"
    return response
