from django.db import transaction
from rest_framework import serializers

from articles.models import Article
from users.serializers import UserSerializer

from .models import ForumCategory, Post, Reply, Thread


class LikeableSerializerMixin:
    """
    Shared like handling for posts and replies.

    Both the count and the "did I like this" flag are read from the prefetched
    likes, never with a fresh query. ``obj.likes.filter(...)`` looks harmless
    but always hits the database, which turned one thread page into one query
    per post plus one per reply.
    """

    def get_likes_count(self, obj):
        return len(obj.likes.all())

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return any(user.id == request.user.id for user in obj.likes.all())


class ForumCategorySerializer(serializers.ModelSerializer):
    """Serializer for forum categories."""

    class Meta:
        model = ForumCategory
        fields = ("id", "name", "slug", "description", "order")
        read_only_fields = ("slug",)


class ReplySerializer(LikeableSerializerMixin, serializers.ModelSerializer):
    """Serializer for replies to posts."""

    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = (
            "id",
            "post",
            "author",
            "content",
            "likes_count",
            "is_liked",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "post", "author", "created_at", "updated_at")


class ReplyWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating and editing replies."""

    class Meta:
        model = Reply
        fields = ("id", "content")
        read_only_fields = ("id",)


class PostSerializer(LikeableSerializerMixin, serializers.ModelSerializer):
    """Serializer for posts with nested replies."""

    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies = ReplySerializer(many=True, read_only=True)
    is_pinned = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "thread",
            "author",
            "content",
            "likes_count",
            "is_liked",
            "is_pinned",
            "replies",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "thread", "author", "created_at", "updated_at")

    def get_is_pinned(self, obj):
        return hasattr(obj, "pinned_entry")


class PostWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating posts."""

    class Meta:
        model = Post
        fields = ("id", "content")
        read_only_fields = ("id",)


class ThreadArticleSerializer(serializers.ModelSerializer):
    """Minimal article representation shown on a thread that quotes one."""

    class Meta:
        model = Article
        fields = ("id", "title", "slug", "cover_image")


class ThreadListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for thread lists."""

    author = UserSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    article = ThreadArticleSerializer(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)
    last_post = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = (
            "id",
            "title",
            "slug",
            "author",
            "category",
            "article",
            "posts_count",
            "last_post",
            "is_pinned",
            "is_closed",
            "views",
            "created_at",
            "updated_at",
        )

    def get_last_post(self, obj):
        """
        Read the last post from annotations set by the view.

        The obvious ``obj.posts.last()`` clones the queryset and so bypasses
        any prefetch, costing one query per thread in the list.
        """
        created_at = getattr(obj, "last_post_at", None)
        if not created_at:
            return None
        return {
            "author": getattr(obj, "last_post_author", None),
            "created_at": created_at,
        }


class ThreadDetailSerializer(serializers.ModelSerializer):
    """Full serializer for thread detail view, includes posts and pinned posts."""

    author = UserSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    article = ThreadArticleSerializer(read_only=True)
    posts = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    pinned_posts = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = (
            "id",
            "title",
            "slug",
            "author",
            "category",
            "article",
            "posts",
            "posts_count",
            "pinned_posts",
            "is_pinned",
            "is_closed",
            "views",
            "created_at",
            "updated_at",
        )

    def get_posts(self, obj):
        return PostSerializer(obj.posts.all(), many=True, context=self.context).data

    def get_posts_count(self, obj):
        return len(obj.posts.all())

    def get_pinned_posts(self, obj):
        """Return pinned posts in pin order, straight from the prefetch."""
        pinned = sorted(obj.pinned_posts.all(), key=lambda p: (p.order, p.pinned_at))
        return PostSerializer(
            [entry.post for entry in pinned], many=True, context=self.context
        ).data


class ThreadWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a thread together with its opening post.

    ``content`` is not a Thread field: it becomes the first post. It is
    therefore accepted on create only — see ThreadUpdateSerializer for edits.
    """

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ForumCategory.objects.all(),
        source="category",
        required=False,
        allow_null=True,
    )
    article_id = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.filter(status=Article.Status.PUBLISHED),
        source="article",
        required=False,
        allow_null=True,
        help_text="Articolo pubblicato da cui nasce il topic, opzionale.",
    )
    content = serializers.CharField(write_only=True)

    class Meta:
        model = Thread
        fields = ("id", "title", "slug", "content", "category_id", "article_id")
        read_only_fields = ("id", "slug")

    @transaction.atomic
    def create(self, validated_data):
        """Create thread and its first post atomically."""
        content = validated_data.pop("content")
        thread = Thread.objects.create(
            author=self.context["request"].user, **validated_data
        )
        Post.objects.create(thread=thread, author=thread.author, content=content)
        return thread


class ThreadUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for editing a thread.

    Deliberately excludes ``content``: the opening post is edited through the
    post endpoints. Reusing the create serializer here silently swallowed the
    submitted content, because Thread has no such field to write it to.
    """

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ForumCategory.objects.all(),
        source="category",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Thread
        fields = ("id", "title", "slug", "category_id")
        read_only_fields = ("id", "slug")
