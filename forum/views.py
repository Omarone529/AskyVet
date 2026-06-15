from django.db.models import F
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from .models import ForumCategory, Thread, Post, PinnedPost
from .permissions import IsAuthorOrAdmin, IsThreadAuthorOrAdmin
from .serializers import (
    ForumCategorySerializer,
    ThreadListSerializer,
    ThreadDetailSerializer,
    ThreadWriteSerializer,
    PostWriteSerializer,
)


class ForumCategoryListView(generics.ListAPIView):
    """List all forum categories. Public."""

    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer


class ThreadListView(generics.ListAPIView):
    """List all threads, ordered by pinned then last activity. Public."""

    serializer_class = ThreadListSerializer

    def get_queryset(self):
        queryset = Thread.objects.select_related("author", "category").prefetch_related(
            "posts"
        )

        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset


class ThreadCreateView(generics.CreateAPIView):
    """Create a new thread. Authenticated only."""

    serializer_class = ThreadWriteSerializer
    permission_classes = [IsAuthenticated]


class ThreadDetailView(generics.RetrieveAPIView):
    """Retrieve a single thread with all posts. Public."""

    serializer_class = ThreadDetailSerializer
    lookup_field = "slug"
    queryset = Thread.objects.select_related("author", "category").prefetch_related(
        "posts__author", "posts__likes", "pinned_posts__post__author"
    )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Thread.objects.filter(id=instance.id).update(views=F("views") + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ThreadUpdateView(generics.UpdateAPIView):
    """Update thread. Admin only."""

    serializer_class = ThreadWriteSerializer
    permission_classes = [IsAdmin]
    lookup_field = "slug"
    queryset = Thread.objects.all()
    http_method_names = ["put", "patch"]


class ThreadDeleteView(generics.DestroyAPIView):
    """Delete a thread. Admin only."""

    permission_classes = [IsAdmin]
    lookup_field = "slug"
    queryset = Thread.objects.all()


class ThreadPinView(APIView):
    """Toggle pin status of a thread. Admin only."""

    permission_classes = [IsAdmin]

    def patch(self, request, slug):
        try:
            thread = Thread.objects.get(slug=slug)
        except Thread.DoesNotExist:
            return Response(
                {"detail": "Thread non trovato."},
                status=status.HTTP_404_NOT_FOUND,
            )

        thread.is_pinned = not thread.is_pinned
        thread.save(update_fields=["is_pinned"])

        action = "pinnato" if thread.is_pinned else "spinnato"
        return Response({"detail": f"Thread {action} con successo."})


class ThreadCloseView(APIView):
    """Toggle close status. Admin only."""

    permission_classes = [IsAdmin]

    def patch(self, request, slug):
        try:
            thread = Thread.objects.get(slug=slug)
        except Thread.DoesNotExist:
            return Response(
                {"detail": "Thread non trovato."},
                status=status.HTTP_404_NOT_FOUND,
            )

        thread.is_closed = not thread.is_closed
        thread.save(update_fields=["is_closed"])

        action = "chiuso" if thread.is_closed else "riaperto"
        return Response({"detail": f"Thread {action} con successo."})


class PostCreateView(generics.CreateAPIView):
    """Create a new post in a thread. Authenticated only."""

    serializer_class = PostWriteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        thread_slug = self.kwargs.get("thread_slug")
        try:
            thread = Thread.objects.get(slug=thread_slug)
        except Thread.DoesNotExist:
            from rest_framework import serializers as drf_serializers

            raise drf_serializers.ValidationError({"detail": "Thread non trovato."})

        if thread.is_closed:
            from rest_framework import serializers as drf_serializers

            raise drf_serializers.ValidationError({"detail": "Questo thread è chiuso."})

        serializer.save(thread=thread, author=self.request.user)
        thread.save(update_fields=["updated_at"])


class PostUpdateView(generics.UpdateAPIView):
    """Update a post. Author or admin only."""

    serializer_class = PostWriteSerializer
    permission_classes = [IsAuthorOrAdmin]
    lookup_field = "id"
    queryset = Post.objects.all()
    http_method_names = ["put", "patch"]


class PostDeleteView(generics.DestroyAPIView):
    """Delete a post. Author or admin only."""

    permission_classes = [IsAuthorOrAdmin]
    lookup_field = "id"
    queryset = Post.objects.all()


class PostLikeView(APIView):
    """Toggle like on a post. Authenticated only."""

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {"detail": "Post non trovato."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True

        return Response({"liked": liked, "likes_count": post.likes.count()})


class PostPinView(APIView):
    """Pin/unpin a post inside a thread. Thread author or admin only."""

    permission_classes = [IsThreadAuthorOrAdmin]

    def post(self, request, post_id):
        try:
            post = Post.objects.select_related("thread__author").get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {"detail": "Post non trovato."},
                status=status.HTTP_404_NOT_FOUND,
            )

        thread = post.thread
        pinned_entry = PinnedPost.objects.filter(post=post, thread=thread).first()

        if pinned_entry:
            pinned_entry.delete()
            return Response({"detail": "Post spinnato con successo."})
        else:
            PinnedPost.objects.create(post=post, thread=thread)
            return Response({"detail": "Post pinnato con successo."})
