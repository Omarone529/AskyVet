from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.permissions import is_admin


class IsAuthorOrAdmin(BasePermission):
    """
    Allow writes only to the author of the object, or to an admin.

    Reads stay open. Used on post and reply endpoints so an author can fix or
    remove what they wrote without going through a moderator.
    """

    message = "Non hai i permessi per questa operazione."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if is_admin(request.user):
            return True
        return bool(request.user.is_authenticated) and obj.author_id == request.user.id


class IsThreadAuthorOrAdmin(BasePermission):
    """
    Allow the thread's author, or an admin, to act on an object inside it.

    Both hooks are implemented on purpose. ``has_object_permission`` alone is
    never invoked by a plain APIView — it only runs when a view calls
    check_object_permissions() — which previously left the pin endpoint open to
    anonymous callers. The has_permission half at least requires a login;
    ownership is then checked per object.
    """

    message = "Solo l'autore del thread o un admin può eseguire questa operazione."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        thread = obj.thread if hasattr(obj, "thread") else obj
        return thread.author_id == request.user.id
