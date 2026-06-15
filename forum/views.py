from rest_framework import serializers as drf_serializers
from django.db.models import F
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from .models import ForumCategory, Thread, Post, PinnedPost, Reply
from .permissions import IsThreadAuthorOrAdmin
from .serializers import (
    ForumCategorySerializer,
    ThreadListSerializer,
    ThreadDetailSerializer,
    ThreadWriteSerializer,
    PostWriteSerializer,
    ReplyWriteSerializer,
)


class ForumCategoryListView(generics.ListAPIView):
    """List all forum categories. Public."""

    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer


class ThreadListView(generics.ListAPIView):
    """List all threads, ordered by pinned then last activity. Public."""

    serializer_class = ThreadListSerializer

    def get_queryset(self):
        """Return threads, optionally filtered by category, with prefetch to avoid N+1."""
        queryset = Thread.objects.select_related("author", "category").prefetch_related(
            "posts",
            "posts__author",  # Fix N+1 su last_post
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
    """Retrieve a single thread with all posts and replies. Public."""

    serializer_class = ThreadDetailSerializer
    lookup_field = "slug"
    queryset = Thread.objects.select_related("author", "category").prefetch_related(
        "posts__author",
        "posts__likes",
        "posts__replies__author",
        "posts__replies__likes",
        "pinned_posts__post__author",
    )

    def retrieve(self, request, *args, **kwargs):
        """Increment view count on each retrieve."""
        instance = self.get_object()
        Thread.objects.filter(id=instance.id).update(views=F("views") + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ThreadUpdateView(generics.UpdateAPIView):
    """Update a thread. Admin only."""

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
        """Toggle is_pinned on the thread."""
        try:
            thread = Thread.objects.get(slug=slug)
        except Thread.DoesNotExist:
            return Response(
                {"detail": "Thread non trovato."}, status=status.HTTP_404_NOT_FOUND
            )

        thread.is_pinned = not thread.is_pinned
        thread.save(update_fields=["is_pinned"])

        action = "pinnato" if thread.is_pinned else "spinnato"
        return Response({"detail": f"Thread {action} con successo."})


class ThreadCloseView(APIView):
    """Toggle close status of a thread. Admin only."""

    permission_classes = [IsAdmin]

    def patch(self, request, slug):
        """Toggle is_closed on the thread."""
        try:
            thread = Thread.objects.get(slug=slug)
        except Thread.DoesNotExist:
            return Response(
                {"detail": "Thread non trovato."}, status=status.HTTP_404_NOT_FOUND
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
        """Attach thread to post and block posting on closed threads."""
        thread_slug = self.kwargs.get("thread_slug")
        try:
            thread = Thread.objects.get(slug=thread_slug)
        except Thread.DoesNotExist:
            raise drf_serializers.ValidationError({"detail": "Thread non trovato."})

        if thread.is_closed:
            raise drf_serializers.ValidationError({"detail": "Questo thread è chiuso."})

        serializer.save(thread=thread, author=self.request.user)
        thread.save(update_fields=["updated_at"])


class PostDeleteView(generics.DestroyAPIView):
    """Delete a post. Admin only."""

    permission_classes = [IsAdmin]
    lookup_field = "id"
    queryset = Post.objects.all()


class PostLikeView(APIView):
    """Toggle like on a post. Authenticated only."""

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        """Toggle like and return updated count."""
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {"detail": "Post non trovato."}, status=status.HTTP_404_NOT_FOUND
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
        """Toggle pinned state of a post."""
        try:
            post = Post.objects.select_related("thread__author").get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {"detail": "Post non trovato."}, status=status.HTTP_404_NOT_FOUND
            )

        thread = post.thread
        pinned_entry = PinnedPost.objects.filter(post=post, thread=thread).first()

        if pinned_entry:
            pinned_entry.delete()
            return Response({"detail": "Post spinnato con successo."})

        PinnedPost.objects.create(post=post, thread=thread)
        return Response({"detail": "Post pinnato con successo."})


class ReplyCreateView(generics.CreateAPIView):
    """Create a reply to a post. Authenticated only."""

    serializer_class = ReplyWriteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Attach post to reply and block replies on closed threads."""
        try:
            post = Post.objects.select_related("thread").get(
                id=self.kwargs.get("post_id")
            )
        except Post.DoesNotExist:
            raise drf_serializers.ValidationError({"detail": "Post non trovato."})

        if post.thread.is_closed:
            raise drf_serializers.ValidationError({"detail": "Questo thread è chiuso."})

        serializer.save(post=post, author=self.request.user)


class ReplyDeleteView(generics.DestroyAPIView):
    """Delete a reply. Admin only."""

    permission_classes = [IsAdmin]
    lookup_field = "id"
    queryset = Reply.objects.all()


class ReplyLikeView(APIView):
    """Toggle like on a reply. Authenticated only."""

    permission_classes = [IsAuthenticated]

    def post(self, request, reply_id):
        """Toggle like and return updated count."""
        try:
            reply = Reply.objects.get(id=reply_id)
        except Reply.DoesNotExist:
            return Response(
                {"detail": "Risposta non trovata."}, status=status.HTTP_404_NOT_FOUND
            )

        if request.user in reply.likes.all():
            reply.likes.remove(request.user)
            liked = False
        else:
            reply.likes.add(request.user)
            liked = True

        return Response({"liked": liked, "likes_count": reply.likes.count()})
