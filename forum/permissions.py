from rest_framework.permissions import BasePermission


class IsAuthorOrAdmin(BasePermission):
    """Allow access only to the author of the resource or admin."""

    message = "Non hai i permessi per questa operazione."

    def has_object_permission(self, request, view, obj):
        """Grant access to admins or the resource author."""
        if request.user and request.user.is_admin:
            return True
        return obj.author == request.user


class IsThreadAuthorOrAdmin(BasePermission):
    """Allow access only to the thread author or admin."""

    message = "Solo l'autore del thread o un admin può eseguire questa operazione."

    def has_object_permission(self, request, view, obj):
        """Grant access to admins or the thread author."""
        if request.user and request.user.is_admin:
            return True
        return obj.thread.author == request.user
