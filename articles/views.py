from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin

from .models import Article, Category, Tag
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticleWriteSerializer,
    CategorySerializer,
    TagSerializer,
)


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    List all categories or create a new one.

    GET  /api/categories/ → public
    POST /api/categories/ → admin only
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        """Allow anyone to read, only admins to write."""
        if self.request.method == "POST":
            return [IsAdmin()]
        return []


class TagListCreateView(generics.ListCreateAPIView):
    """
    List all tags or create a new one.

    GET  /api/tags/ → public
    POST /api/tags/ → admin only
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_permissions(self):
        """Allow anyone to read, only admins to write."""
        if self.request.method == "POST":
            return [IsAdmin()]
        return []


class ArticleListView(generics.ListAPIView):
    """
    List all published articles.

    GET /api/articles/ → public, supports filtering by category and tag.
    """

    serializer_class = ArticleListSerializer

    def get_queryset(self):
        """Return published articles, optionally filtered by category or tag slug."""
        queryset = Article.objects.filter(status=Article.Status.PUBLISHED)

        category = self.request.query_params.get("category")
        tag = self.request.query_params.get("tag")

        if category:
            queryset = queryset.filter(category__slug=category)
        if tag:
            queryset = queryset.filter(tags__slug=tag)

        return queryset


class ArticleDraftListView(generics.ListAPIView):
    """
    List all draft articles. Admin only.

    GET /api/articles/drafts/ → admin only.
    """

    serializer_class = ArticleListSerializer
    permission_classes = [IsAdmin]
    queryset = Article.objects.filter(status=Article.Status.DRAFT)


class ArticleDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single published article by slug.

    GET /api/articles/<slug>/ → public.
    """

    serializer_class = ArticleDetailSerializer
    lookup_field = "slug"
    queryset = Article.objects.filter(status=Article.Status.PUBLISHED)


class ArticleCreateView(generics.CreateAPIView):
    """
    Create a new article. Admin only.

    POST /api/articles/ → admin only.
    Supports multipart/form-data for image uploads.
    """

    serializer_class = ArticleWriteSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]


class ArticleUpdateView(generics.UpdateAPIView):
    """
    Update an existing article. Admin only.

    PUT /api/articles/<slug>/ → admin only.
    Supports multipart/form-data for image uploads.
    """

    serializer_class = ArticleWriteSerializer
    permission_classes = [IsAdmin]
    lookup_field = "slug"
    queryset = Article.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["put", "patch"]


class ArticleDeleteView(generics.DestroyAPIView):
    """
    Delete an article. Admin only.

    DELETE /api/articles/<slug>/ → admin only.
    """

    permission_classes = [IsAdmin]
    lookup_field = "slug"
    queryset = Article.objects.all()


class ArticlePublishView(APIView):
    """
    Publish a draft article. Admin only.

    PATCH /api/articles/<slug>/publish/ → sets status to published
    and records the publication timestamp.
    """

    permission_classes = [IsAdmin]

    def patch(self, request, slug):
        """Toggle article status between draft and published."""
        try:
            article = Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            return Response(
                {"detail": "Articolo non trovato."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if article.status == Article.Status.PUBLISHED:
            article.status = Article.Status.DRAFT
            article.published_at = None
            message = "Articolo riportato in bozza."
        else:
            article.status = Article.Status.PUBLISHED
            article.published_at = timezone.now()
            message = "Articolo pubblicato con successo."

        article.save(update_fields=["status", "published_at"])
        return Response({"detail": message})
