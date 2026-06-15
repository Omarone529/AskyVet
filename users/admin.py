from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = ("email", "username", "is_admin", "is_active", "created_at")
    list_filter = ("is_admin", "is_active")
    search_fields = ("email", "username")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "email", "username", "password")}),
        ("Avatar", {"fields": ("avatar",)}),
        ("Permessi", {"fields": ("is_admin", "is_active", "is_staff", "is_superuser")}),
        ("Google OAuth", {"fields": ("google_id",)}),
        ("Date", {"fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "is_admin"),
            },
        ),
    )
