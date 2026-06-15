from django.contrib import admin

from .models import ForumCategory, Thread, Post, PinnedPost


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "is_pinned",
        "is_closed",
        "created_at",
    )
    list_filter = ("is_pinned", "is_closed", "category")
    search_fields = ("title", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views", "created_at", "updated_at")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username", "thread__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PinnedPost)
class PinnedPostAdmin(admin.ModelAdmin):
    list_display = ("post", "thread", "pinned_at", "order")
    list_filter = ("pinned_at",)
    search_fields = ("post__content", "thread__title")
