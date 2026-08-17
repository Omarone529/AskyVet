from django.db.models import Count, F, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import parse_bool
from users.permissions import IsAdmin, IsNotMuted

from .models import ForumCategory, PinnedPost, Post, Reply, Thread
from .permissions import IsAuthorOrAdmin, IsThreadAuthorOrAdmin
from .serializers import (
    ForumCategorySerializer,
    PostSerializer,
    PostWriteSerializer,
    ReplySerializer,
    ReplyWriteSerializer,
    ThreadDetailSerializer,
    ThreadListSerializer,
    ThreadUpdateSerializer,
    ThreadWriteSerializer,
)

# Prefetch chain used by every endpoint that renders posts. Likes are pulled in
# so the serializer can count them and answer "did I like this" from memory.
POST_PREFETCH = (
    "posts__author",
    "posts__likes",
    "posts__pinned_entry",
    "posts__replies__author",
    "posts__replies__likes",
    "pinned_posts__post__author",
    "pinned_posts__post__likes",
)


class ForumCategoryListView(generics.ListCreateAPIView):
    """
    List forum categories, or create one.

    GET  /api/forum/categories/ → public
    POST /api/forum/categories/ → admin only
    """

    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [AllowAny()]


class ThreadListCreateView(generics.ListCreateAPIView):
    """
    List threads, or open a new one.

    GET  /api/forum/threads/ → public. Filters: ?category=<slug>
                               ?article=<uuid> ?search=<text>
    POST /api/forum/threads/ → authenticated, non-muted users.
    """

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ThreadWriteSerializer
        return ThreadListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsNotMuted()]
        return [AllowAny()]

    def get_queryset(self):
        """
        Threads with their post count and last activity resolved in SQL.

        Counting posts in Python meant prefetching every post of every thread
        just to render a list; a Count plus two Subqueries keeps the whole page
        to a single query.
        """
        last_post = Post.objects.filter(thread=OuterRef("pk")).order_by("-created_at")

        queryset = Thread.objects.select_related(
            "author", "category", "article"
        ).annotate(
            posts_count=Count("posts", distinct=True),
            last_post_at=Subquery(last_post.values("created_at")[:1]),
            last_post_author=Subquery(last_post.values("author__username")[:1]),
        )

        category_slug = self.request.query_params.get("category")
        article_id = self.request.query_params.get("article")
        search = self.request.query_params.get("search")

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        if search:
            queryset = queryset.filter(title__icontains=search)

        # Explicit: the annotations introduce a GROUP BY, which drops the
        # model's Meta ordering. Without it the paginator warns and rows can
        # repeat or vanish across pages.
        return queryset.order_by("-is_pinned", "-updated_at")


class ThreadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, edit or delete a thread.

    GET              → public
    PUT/PATCH/DELETE → thread author or admin
    """

    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ThreadUpdateSerializer
        return ThreadDetailSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdmin()]

    def get_queryset(self):
        return Thread.objects.select_related(
            "author", "category", "article"
        ).prefetch_related(*POST_PREFETCH)

    def retrieve(self, request, *args, **kwargs):
        """Increment the view counter, then return the fresh value."""
        instance = self.get_object()
        Thread.objects.filter(pk=instance.pk).update(views=F("views") + 1)

        # The UPDATE above runs in SQL and leaves the in-memory instance stale,
        # so the response would otherwise always be one view behind.
        instance.views += 1

        return Response(self.get_serializer(instance).data)


class ThreadPinView(APIView):
    """
    Pin or unpin a thread. Admin only.

    PATCH /api/forum/threads/<slug>/pin/ → {"pinned": true}
    """

    permission_classes = [IsAdmin]

    def patch(self, request, slug):
        thread = get_object_or_404(Thread, slug=slug)
        thread.is_pinned = parse_bool(request.data.get("pinned"))
        thread.save(update_fields=["is_pinned"])

        return Response(
            {
                "detail": "Thread pinnato." if thread.is_pinned else "Thread spinnato.",
                "is_pinned": thread.is_pinned,
            }
        )


class ThreadCloseView(APIView):
    """
    Close or reopen a thread. Admin only.

    PATCH /api/forum/threads/<slug>/close/ → {"closed": true}
    """

    permission_classes = [IsAdmin]

    def patch(self, request, slug):
        thread = get_object_or_404(Thread, slug=slug)
        thread.is_closed = parse_bool(request.data.get("closed"))
        thread.save(update_fields=["is_closed"])

        return Response(
            {
                "detail": "Thread chiuso." if thread.is_closed else "Thread riaperto.",
                "is_closed": thread.is_closed,
            }
        )


class PostListCreateView(generics.ListCreateAPIView):
    """
    List the posts of a thread, or add one.

    GET  /api/forum/threads/<slug>/posts/ → public
    POST /api/forum/threads/<slug>/posts/ → authenticated, non-muted users
    """

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostWriteSerializer
        return PostSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsNotMuted()]
        return [AllowAny()]

    def get_queryset(self):
        return (
            Post.objects.filter(thread__slug=self.kwargs["thread_slug"])
            .select_related("author")
            .prefetch_related(
                "likes", "pinned_entry", "replies__author", "replies__likes"
            )
        )

    def perform_create(self, serializer):
        """Attach the thread to the post and refuse posting on closed threads."""
        thread = get_object_or_404(Thread, slug=self.kwargs["thread_slug"])

        if thread.is_closed:
            raise ValidationError({"detail": "Questo thread è chiuso."})

        serializer.save(thread=thread, author=self.request.user)
        # Bumps updated_at (auto_now), which is what orders the thread list.
        thread.save(update_fields=["updated_at"])


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, edit or delete a post.

    GET              → public
    PUT/PATCH/DELETE → the post's author, or an admin
    """

    lookup_url_kwarg = "post_id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return PostWriteSerializer
        return PostSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdmin()]

    def get_queryset(self):
        return Post.objects.select_related("author", "thread").prefetch_related(
            "likes", "pinned_entry", "replies__author", "replies__likes"
        )


class PostLikeView(APIView):
    """
    Toggle a like on a post.

    POST /api/forum/posts/<post_id>/like/
    Muted users may still like — a mute only blocks publishing.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True

        return Response({"liked": liked, "likes_count": post.likes.count()})


class PostPinView(APIView):
    """
    Pin or unpin a post inside its thread. Thread author or admin only.

    POST /api/forum/posts/<post_id>/pin/

    check_object_permissions is called explicitly: a plain APIView never
    invokes it on its own, which previously left this endpoint wide open to
    anonymous callers despite the declared permission class.
    """

    permission_classes = [IsAuthenticated, IsThreadAuthorOrAdmin]

    def post(self, request, post_id):
        post = get_object_or_404(
            Post.objects.select_related("thread__author"), id=post_id
        )
        self.check_object_permissions(request, post)

        pinned_entry = PinnedPost.objects.filter(post=post).first()
        if pinned_entry:
            pinned_entry.delete()
            return Response({"detail": "Post spinnato con successo.", "pinned": False})

        PinnedPost.objects.create(post=post, thread=post.thread)
        return Response({"detail": "Post pinnato con successo.", "pinned": True})


class ReplyListCreateView(generics.ListCreateAPIView):
    """
    List the replies of a post, or add one.

    GET  /api/forum/posts/<post_id>/replies/ → public
    POST /api/forum/posts/<post_id>/replies/ → authenticated, non-muted users
    """

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReplyWriteSerializer
        return ReplySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsNotMuted()]
        return [AllowAny()]

    def get_queryset(self):
        return (
            Reply.objects.filter(post_id=self.kwargs["post_id"])
            .select_related("author")
            .prefetch_related("likes")
        )

    def perform_create(self, serializer):
        """Attach the post to the reply and refuse replies on closed threads."""
        post = get_object_or_404(
            Post.objects.select_related("thread"), id=self.kwargs["post_id"]
        )

        if post.thread.is_closed:
            raise ValidationError({"detail": "Questo thread è chiuso."})

        serializer.save(post=post, author=self.request.user)
        post.thread.save(update_fields=["updated_at"])


class ReplyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, edit or delete a reply.

    GET              → public
    PUT/PATCH/DELETE → the reply's author, or an admin
    """

    lookup_url_kwarg = "reply_id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ReplyWriteSerializer
        return ReplySerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdmin()]

    def get_queryset(self):
        return Reply.objects.select_related("author").prefetch_related("likes")


class ReplyLikeView(APIView):
    """
    Toggle a like on a reply.

    POST /api/forum/replies/<reply_id>/like/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, reply_id):
        reply = get_object_or_404(Reply, id=reply_id)

        if reply.likes.filter(id=request.user.id).exists():
            reply.likes.remove(request.user)
            liked = False
        else:
            reply.likes.add(request.user)
            liked = True

        return Response({"liked": liked, "likes_count": reply.likes.count()})
