from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to admin users."""

    message = "Accesso riservato agli amministratori."

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_admin
        )


class IsSelf(BasePermission):
    """Allow access only to the owner of the resource."""

    message = "Puoi modificare solo il tuo profilo."

    def has_object_permission(self, request, view, obj):
        return obj == request.user
