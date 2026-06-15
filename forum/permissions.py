from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrAdmin(BasePermission):
    """Allow access only to the author of the resource or admin."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_admin:
            return True
        return obj.author == request.user


class IsAuthenticatedOrReadOnly(BasePermission):
    """Read-only for unauthenticated users, write requires auth."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsThreadAuthorOrAdmin(BasePermission):
    """Allow access only to the thread author or admin."""

    def has_permission(self, request, view):
        if request.user and request.user.is_admin:
            return True

        post_id = view.kwargs.get("post_id")
        if not post_id:
            return False

        from .models import Post

        try:
            post = Post.objects.select_related("thread__author").get(id=post_id)
            return post.thread.author == request.user
        except Post.DoesNotExist:
            return False
