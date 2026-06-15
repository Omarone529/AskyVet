from django.urls import path

from .views import (
    ForumCategoryListView,
    ThreadListView,
    ThreadCreateView,
    ThreadDetailView,
    ThreadUpdateView,
    ThreadDeleteView,
    ThreadPinView,
    ThreadCloseView,
    PostCreateView,
    PostDeleteView,
    PostLikeView,
    PostPinView,
    ReplyCreateView,
    ReplyDeleteView,
    ReplyLikeView,
)

urlpatterns = [
    # Forum categories
    path("categories/", ForumCategoryListView.as_view(), name="forum-categories"),
    # Threads
    path("threads/", ThreadListView.as_view(), name="thread-list"),
    path("threads/create/", ThreadCreateView.as_view(), name="thread-create"),
    path("threads/<slug:slug>/", ThreadDetailView.as_view(), name="thread-detail"),
    path(
        "threads/<slug:slug>/update/", ThreadUpdateView.as_view(), name="thread-update"
    ),
    path(
        "threads/<slug:slug>/delete/", ThreadDeleteView.as_view(), name="thread-delete"
    ),
    path("threads/<slug:slug>/pin/", ThreadPinView.as_view(), name="thread-pin"),
    path("threads/<slug:slug>/close/", ThreadCloseView.as_view(), name="thread-close"),
    # Posts
    path(
        "threads/<slug:thread_slug>/posts/create/",
        PostCreateView.as_view(),
        name="post-create",
    ),
    path("posts/<int:id>/delete/", PostDeleteView.as_view(), name="post-delete"),
    path("posts/<int:post_id>/like/", PostLikeView.as_view(), name="post-like"),
    path("posts/<int:post_id>/pin/", PostPinView.as_view(), name="post-pin"),
    # Replies
    path(
        "posts/<int:post_id>/replies/create/",
        ReplyCreateView.as_view(),
        name="reply-create",
    ),
    path("replies/<int:id>/delete/", ReplyDeleteView.as_view(), name="reply-delete"),
    path("replies/<int:reply_id>/like/", ReplyLikeView.as_view(), name="reply-like"),
]
