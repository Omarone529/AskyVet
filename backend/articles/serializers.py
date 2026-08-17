from django.utils import timezone
from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Article, Category, Tag


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description")
        read_only_fields = ("slug",)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")
        read_only_fields = ("slug",)


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for article lists.

    Used in list views to avoid fetching the full body for each article.
    """

    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = (
            "id",
            "author",
            "title",
            "slug",
            "cover_image",
            "category",
            "tags",
            "status",
            "published_at",
            "created_at",
        )


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for article detail view.

    Includes the body field, used only when fetching a single article, plus a
    pointer to the forum discussion attached to the article, if any.
    """

    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    discussion = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            "id",
            "author",
            "title",
            "slug",
            "body",
            "cover_image",
            "category",
            "tags",
            "status",
            "discussion",
            "published_at",
            "created_at",
            "updated_at",
        )

    def get_discussion(self, obj):
        """
        Return the forum thread discussing this article, if one exists.

        Lets the article page link straight to the conversation instead of
        carrying a comment system of its own.
        """
        thread = obj.threads.first()
        if not thread:
            return None
        return {
            "id": thread.id,
            "slug": thread.slug,
            "title": thread.title,
            "posts_count": thread.posts.count(),
        }


class ArticleWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating articles.

    Accepts category and tags as IDs for writing,
    while read serializers return nested objects.
    """

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        required=False,
        allow_null=True,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source="tags",
        many=True,
        required=False,
    )

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "slug",
            "body",
            "cover_image",
            "category_id",
            "tag_ids",
            "status",
            "published_at",
        )
        read_only_fields = ("id", "slug", "published_at")

    def create(self, validated_data):
        """Assign the requesting user as author on creation."""
        validated_data["author"] = self.context["request"].user

        if validated_data.get("status") == Article.Status.PUBLISHED:
            validated_data["published_at"] = timezone.now()

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Keep published_at in step with status.

        Promoting a draft stamps the publication time; sending an article back
        to draft clears it. Without this an article published through an update
        would keep published_at = None and sort to the bottom of every list.
        """
        new_status = validated_data.get("status", instance.status)

        if new_status == Article.Status.PUBLISHED and instance.published_at is None:
            validated_data["published_at"] = timezone.now()
        elif new_status == Article.Status.DRAFT:
            validated_data["published_at"] = None

        return super().update(instance, validated_data)
