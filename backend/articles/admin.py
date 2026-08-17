from django.contrib import admin

from .models import Article, Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""

    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for Tag model."""

    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin configuration for Article model."""

    list_display = (
        "title",
        "author",
        "category",
        "status",
        "published_at",
        "created_at",
    )
    list_filter = ("status", "category", "tags")
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    filter_horizontal = ("tags",)

    fieldsets = (
        (None, {"fields": ("id", "author", "title", "slug", "status")}),
        ("Contenuto", {"fields": ("body", "cover_image")}),
        ("Classificazione", {"fields": ("category", "tags")}),
        ("Date", {"fields": ("published_at", "created_at", "updated_at")}),
    )
