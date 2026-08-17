from django.urls import path

from .views import (
    ForumCategoryListView,
    PostDetailView,
    PostLikeView,
    PostListCreateView,
    PostPinView,
    ReplyDetailView,
    ReplyLikeView,
    ReplyListCreateView,
    ThreadCloseView,
    ThreadDetailView,
    ThreadListCreateView,
    ThreadPinView,
)

# As in articles/urls.py, every literal segment precedes the <slug:slug>
# pattern that would otherwise swallow it.
urlpatterns = [
    # Forum categories
    path("categories/", ForumCategoryListView.as_view(), name="forum-categories"),
    # Threads
    path("threads/", ThreadListCreateView.as_view(), name="thread-list"),
    path(
        "threads/<slug:thread_slug>/posts/",
        PostListCreateView.as_view(),
        name="post-list",
    ),
    path("threads/<slug:slug>/pin/", ThreadPinView.as_view(), name="thread-pin"),
    path("threads/<slug:slug>/close/", ThreadCloseView.as_view(), name="thread-close"),
    path("threads/<slug:slug>/", ThreadDetailView.as_view(), name="thread-detail"),
    # Posts
    path(
        "posts/<int:post_id>/replies/",
        ReplyListCreateView.as_view(),
        name="reply-list",
    ),
    path("posts/<int:post_id>/like/", PostLikeView.as_view(), name="post-like"),
    path("posts/<int:post_id>/pin/", PostPinView.as_view(), name="post-pin"),
    path("posts/<int:post_id>/", PostDetailView.as_view(), name="post-detail"),
    # Replies
    path("replies/<int:reply_id>/like/", ReplyLikeView.as_view(), name="reply-like"),
    path("replies/<int:reply_id>/", ReplyDetailView.as_view(), name="reply-detail"),
]
