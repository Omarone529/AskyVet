from django.urls import path

from .views import (
    ArticleDetailView,
    ArticleDraftListView,
    ArticleListCreateView,
    ArticlePublishView,
    CategoryDetailView,
    CategoryListCreateView,
    TagDetailView,
    TagListCreateView,
)

# Order matters: <slug:slug> matches any single segment, so every literal route
# has to be declared before it or Django resolves the literal to the detail
# view. This is what made /api/articles/drafts/ return 404.
urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path("tags/", TagListCreateView.as_view(), name="tag-list"),
    path("tags/<slug:slug>/", TagDetailView.as_view(), name="tag-detail"),
    path("drafts/", ArticleDraftListView.as_view(), name="article-drafts"),
    path("", ArticleListCreateView.as_view(), name="article-list"),
    path("<slug:slug>/publish/", ArticlePublishView.as_view(), name="article-publish"),
    path("<slug:slug>/", ArticleDetailView.as_view(), name="article-detail"),
]
