from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import LoginView as BaseLoginView
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .serializers import (
    AdminCreateSerializer,
    AdminUserSerializer,
    BanSerializer,
    MuteSerializer,
    RegisterSerializer,
    UserDetailSerializer,
)


class LoginView(BaseLoginView):
    """
    Exchange email and password for a JWT pair.

    POST /api/auth/login/ → {"access": ..., "refresh": ..., "user": {...}}
    Throttled to keep credential stuffing expensive.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class GoogleLoginView(SocialLoginView):
    """
    Sign in with a Google OAuth2 access token.

    POST /api/auth/google/ → {"access_token": "..."} returns the same JWT pair
    as the password login. Requires GOOGLE_CLIENT_ID; the secret is only needed
    if the frontend ever switches to sending an authorization code instead.
    """

    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterView(generics.CreateAPIView):
    """
    Handle user registration. Public endpoint.

    POST /api/users/register/ — always creates a non-privileged account.
    """

    serializer_class = RegisterSerializer
    # Required: the project default is IsAuthenticatedOrReadOnly, under which a
    # POST from an anonymous visitor is refused — so nobody could ever sign up.
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class MeView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.

    GET   /api/users/me/ → returns the user's profile.
    PATCH /api/users/me/ → updates the user's profile.
    """

    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user


class UserListView(generics.ListAPIView):
    """
    List all users. Admin only.

    GET /api/users/ → paginated list, filterable with ?search= and ?status=.
    """

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = User.objects.all().order_by("-created_at")

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(username__icontains=search)

        status_filter = self.request.query_params.get("status")
        if status_filter == "banned":
            queryset = queryset.filter(is_active=False)
        elif status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "admin":
            queryset = queryset.filter(is_admin=True)

        return queryset


class AdminCreateView(generics.CreateAPIView):
    """
    Create another administrator. Admin only.

    POST /api/users/admins/ → {"email", "username", "password", "password_confirm"}
    """

    serializer_class = AdminCreateSerializer
    permission_classes = [IsAdmin]


class ModerationView(APIView):
    """Base for moderation actions, which always target another user."""

    permission_classes = [IsAdmin]

    def get_target(self, request, pk):
        """
        Resolve the user being moderated.

        Returns (user, error_response). Admins are off limits, and so is the
        moderator's own account — a self-ban would lock the platform's owner
        out of their own site.
        """
        user = get_object_or_404(User, pk=pk)

        if user == request.user:
            return None, Response(
                {"detail": "Non puoi applicare provvedimenti a te stesso."}, status=403
            )
        if user.is_admin:
            return None, Response(
                {"detail": "Non puoi applicare provvedimenti a un amministratore."},
                status=403,
            )
        return user, None


class BanUserView(ModerationView):
    """
    Ban or reinstate a user. Admin only.

    PATCH /api/users/<id>/ban/ → {"banned": true, "reason": "spam"}

    The action is explicit rather than a toggle, so two moderators acting at
    once cannot accidentally undo each other.
    """

    def patch(self, request, pk):
        user, error = self.get_target(request, pk)
        if error:
            return error

        serializer = BanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        banned = serializer.validated_data["banned"]
        user.is_active = not banned
        user.moderation_reason = serializer.validated_data["reason"] if banned else ""
        user.save(update_fields=["is_active", "moderation_reason", "updated_at"])

        return Response(
            {
                "detail": "Utente bannato." if banned else "Utente riattivato.",
                "user": AdminUserSerializer(user).data,
            }
        )


class MuteUserView(ModerationView):
    """
    Mute a user for a number of hours, or lift an existing mute. Admin only.

    PATCH /api/users/<id>/mute/ → {"hours": 24, "reason": "toni aggressivi"}
    ``hours: 0`` removes the mute.
    """

    def patch(self, request, pk):
        user, error = self.get_target(request, pk)
        if error:
            return error

        serializer = MuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        until = serializer.muted_until()
        user.muted_until = until
        user.moderation_reason = (
            serializer.validated_data["reason"] if until else user.moderation_reason
        )
        user.save(update_fields=["muted_until", "moderation_reason", "updated_at"])

        detail = (
            f"Utente silenziato fino al {until:%d/%m/%Y %H:%M}."
            if until
            else "Limitazione rimossa."
        )
        return Response({"detail": detail, "user": AdminUserSerializer(user).data})
