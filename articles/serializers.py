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

    Includes the body field, used only when fetching a single article.
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
            "body",
            "cover_image",
            "category",
            "tags",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        )


class ArticleWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating articles.

    Accepts category and tags as IDs for writing,
    while read serializers return nested objects.
    """

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
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
            "title",
            "body",
            "cover_image",
            "category_id",
            "tag_ids",
            "status",
        )

    def create(self, validated_data):
        """Assign the requesting user as author on creation."""
        validated_data["author"] = self.context["request"].user

        # Set published_at if article is created as published
        if validated_data.get("status") == Article.Status.PUBLISHED:
            validated_data["published_at"] = timezone.now()

        return super().create(validated_data)
