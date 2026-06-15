from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for public user data."""

    class Meta:
        model = User
        fields = ("id", "username", "avatar", "created_at")


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for the authenticated user's own profile."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "avatar",
            "is_admin",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "email", "is_admin", "created_at", "updated_at")


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password confirmation."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "username", "password", "password_confirm")

    def validate(self, attrs):
        """Check that the two passwords match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Le password non corrispondono."}
            )
        return attrs

    def create(self, validated_data):
        """Create a new user, removing password_confirm before saving."""
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin operations on users (list, ban/unban)."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "avatar",
            "is_admin",
            "is_active",
            "created_at",
        )
        read_only_fields = (
            "id",
            "email",
            "username",
            "avatar",
            "is_admin",
            "created_at",
        )
