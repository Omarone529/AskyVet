from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import parse_bool
from users.permissions import IsAdmin, is_admin

from .models import Article, Category, Tag
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticleWriteSerializer,
    CategorySerializer,
    TagSerializer,
)


class AdminWriteMixin:
    """Public reads, admin-only writes."""

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdmin()]


class CategoryListCreateView(AdminWriteMixin, generics.ListCreateAPIView):
    """
    List all categories or create a new one.

    GET  /api/articles/categories/ → public
    POST /api/articles/categories/ → admin only
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetailView(AdminWriteMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, edit or delete a category. Writes are admin only."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"


class TagListCreateView(AdminWriteMixin, generics.ListCreateAPIView):
    """
    List all tags or create a new one.

    GET  /api/articles/tags/ → public
    POST /api/articles/tags/ → admin only
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagDetailView(AdminWriteMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, edit or delete a tag. Writes are admin only."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"


class ArticleListCreateView(AdminWriteMixin, generics.ListCreateAPIView):
    """
    List published articles, or create one.

    GET  /api/articles/ → public. Filters: ?category=<slug> ?tag=<slug>
                          ?search=<text>. Admins may add ?status=draft|all.
    POST /api/articles/ → admin only, multipart for the cover image.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ArticleWriteSerializer
        return ArticleListSerializer

    def get_queryset(self):
        queryset = Article.objects.select_related(
            "author", "category"
        ).prefetch_related("tags")

        # Drafts are visible to admins only, and only when asked for.
        requested = self.request.query_params.get("status")
        if is_admin(self.request.user) and requested in ("draft", "all"):
            if requested == "draft":
                queryset = queryset.filter(status=Article.Status.DRAFT)
        else:
            queryset = queryset.filter(status=Article.Status.PUBLISHED)

        category = self.request.query_params.get("category")
        tag = self.request.query_params.get("tag")
        search = self.request.query_params.get("search")

        if category:
            queryset = queryset.filter(category__slug=category)
        if tag:
            queryset = queryset.filter(tags__slug=tag)
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset.distinct()


class ArticleDraftListView(generics.ListAPIView):
    """
    List draft articles. Admin only.

    GET /api/articles/drafts/
    """

    serializer_class = ArticleListSerializer
    permission_classes = [IsAdmin]
    queryset = (
        Article.objects.filter(status=Article.Status.DRAFT)
        .select_related("author", "category")
        .prefetch_related("tags")
    )


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, edit or delete a single article by slug.

    GET    /api/articles/<slug>/ → public for published articles;
                                   admins additionally see drafts.
    PUT/PATCH/DELETE             → admin only.
    """

    lookup_field = "slug"
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ArticleWriteSerializer
        return ArticleDetailSerializer

    def get_queryset(self):
        queryset = Article.objects.select_related(
            "author", "category"
        ).prefetch_related("tags", "threads")
        if is_admin(self.request.user):
            return queryset
        return queryset.filter(status=Article.Status.PUBLISHED)


class ArticlePublishView(APIView):
    """
    Publish or unpublish an article. Admin only.

    PATCH /api/articles/<slug>/publish/ → {"published": true}

    Explicit rather than a toggle, so a repeated call is idempotent instead of
    flipping the article back into a draft.
    """

    permission_classes = [IsAdmin]

    def patch(self, request, slug):
        try:
            article = Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            return Response(
                {"detail": "Articolo non trovato."},
                status=status.HTTP_404_NOT_FOUND,
            )

        published = parse_bool(request.data.get("published"))

        if published:
            article.status = Article.Status.PUBLISHED
            article.published_at = article.published_at or timezone.now()
            message = "Articolo pubblicato con successo."
        else:
            article.status = Article.Status.DRAFT
            article.published_at = None
            message = "Articolo riportato in bozza."

        article.save(update_fields=["status", "published_at", "updated_at"])
        return Response(
            {"detail": message, "article": ArticleDetailSerializer(article).data}
        )
