from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin(user):
    """
    True when ``user`` is a logged-in platform administrator.

    Anonymous users have no ``is_admin`` attribute, so a bare ``user.is_admin``
    raises AttributeError and turns a 403 into a 500. Every permission in the
    project goes through this helper instead.
    """
    return bool(user and user.is_authenticated and user.is_admin)


class IsAdmin(BasePermission):
    """Allow access only to admin users."""

    message = "Accesso riservato agli amministratori."

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsSelf(BasePermission):
    """Allow access only to the owner of the resource."""

    message = "Puoi modificare solo il tuo profilo."

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsNotMuted(BasePermission):
    """
    Block writes from muted users while leaving reads untouched.

    A muted user can still browse the site and like content; only the actions
    that create or change content are refused.
    """

    message = "Sei temporaneamente silenziato e non puoi pubblicare contenuti."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user and user.is_authenticated and user.is_muted:
            self.message = (
                "Sei silenziato fino al "
                f"{user.muted_until:%d/%m/%Y %H:%M} e non puoi pubblicare contenuti."
            )
            return False
        return True
