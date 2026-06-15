from rest_framework import serializers

from users.serializers import UserSerializer
from .models import ForumCategory, Thread, Post, Reply


class ForumCategorySerializer(serializers.ModelSerializer):
    """Serializer for forum categories."""

    class Meta:
        model = ForumCategory
        fields = ("id", "name", "slug", "description", "order")


class ReplySerializer(serializers.ModelSerializer):
    """Serializer for replies to posts."""

    author = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = (
            "id",
            "author",
            "content",
            "likes_count",
            "is_liked",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")

    def get_is_liked(self, obj):
        """Return whether the requesting user has liked this reply."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class ReplyWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating replies."""

    class Meta:
        model = Reply
        fields = ("content",)


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts with nested replies."""

    author = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    is_liked = serializers.SerializerMethodField()
    replies = ReplySerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "thread",
            "author",
            "content",
            "likes_count",
            "is_liked",
            "replies",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "thread", "author", "created_at", "updated_at")

    def get_is_liked(self, obj):
        """Return whether the requesting user has liked this post."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class PostWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating posts."""

    class Meta:
        model = Post
        fields = ("content",)


class ThreadListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for thread lists."""

    author = UserSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    posts_count = serializers.IntegerField(source="posts.count", read_only=True)
    last_post = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = (
            "id",
            "title",
            "slug",
            "author",
            "category",
            "posts_count",
            "last_post",
            "is_pinned",
            "is_closed",
            "views",
            "created_at",
            "updated_at",
        )

    def get_last_post(self, obj):
        """Return author and timestamp of the last post in the thread."""
        last_post = obj.posts.last()
        if last_post:
            return {
                "author": last_post.author.username,
                "created_at": last_post.created_at,
            }
        return None


class ThreadDetailSerializer(serializers.ModelSerializer):
    """Full serializer for thread detail view, includes posts and pinned posts."""

    author = UserSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    posts = PostSerializer(many=True, read_only=True)
    posts_count = serializers.IntegerField(source="posts.count", read_only=True)
    pinned_posts = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = (
            "id",
            "title",
            "slug",
            "author",
            "category",
            "posts",
            "posts_count",
            "pinned_posts",
            "is_pinned",
            "is_closed",
            "views",
            "created_at",
            "updated_at",
        )

    def get_pinned_posts(self, obj):
        """Return pinned posts with their content."""
        pinned = obj.pinned_posts.select_related("post__author").order_by(
            "order", "pinned_at"
        )
        return [
            {
                "id": p.post.id,
                "content": p.post.content,
                "author": UserSerializer(p.post.author).data,
                "created_at": p.post.created_at,
                "pinned_at": p.pinned_at,
            }
            for p in pinned
        ]


class ThreadWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating threads with first post."""

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ForumCategory.objects.all(),
        source="category",
        required=False,
        allow_null=True,
    )
    content = serializers.CharField(write_only=True)

    class Meta:
        model = Thread
        fields = ("title", "content", "category_id")

    def create(self, validated_data):
        """Create thread and its first post atomically."""
        content = validated_data.pop("content")
        thread = Thread.objects.create(
            author=self.context["request"].user, **validated_data
        )
        Post.objects.create(thread=thread, author=thread.author, content=content)
        return thread
