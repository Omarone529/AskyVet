from django.urls import path

from .views import (
    ArticleCreateView,
    ArticleDeleteView,
    ArticleDetailView,
    ArticleDraftListView,
    ArticleListView,
    ArticlePublishView,
    ArticleUpdateView,
    CategoryListCreateView,
    TagListCreateView,
)

urlpatterns = [
    # Public endpoints
    path("categories/", CategoryListCreateView.as_view(), name="category-list"),
    path("tags/", TagListCreateView.as_view(), name="tag-list"),
    path("", ArticleListView.as_view(), name="article-list"),
    path("<slug:slug>/", ArticleDetailView.as_view(), name="article-detail"),
    # Admin only endpoints
    path("drafts/", ArticleDraftListView.as_view(), name="article-drafts"),
    path("create/", ArticleCreateView.as_view(), name="article-create"),
    path("<slug:slug>/update/", ArticleUpdateView.as_view(), name="article-update"),
    path("<slug:slug>/delete/", ArticleDeleteView.as_view(), name="article-delete"),
    path("<slug:slug>/publish/", ArticlePublishView.as_view(), name="article-publish"),
]
