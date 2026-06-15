from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .serializers import (
    AdminUserSerializer,
    RegisterSerializer,
    UserDetailSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Handle user registration. Public endpoint."""

    serializer_class = RegisterSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.

    GET  /api/users/me/ → returns the user's profile.
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

    GET /api/users/ → returns a list of all users.
    """

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all().order_by("-created_at")


class BanUserView(APIView):
    """
    Toggle ban/unban for a user. Admin only.

    PATCH /api/users/<id>/ban/ → toggles is_active on the target user.
    """

    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        """Toggle the active status of a user."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "Utente non trovato."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_admin:
            return Response(
                {"detail": "Non puoi bannare un amministratore."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        action = "bannato" if not user.is_active else "riattivato"
        return Response({"detail": f"Utente {action} con successo."})
