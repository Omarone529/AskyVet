from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for public user data."""

    class Meta:
        model = User
        fields = ("id", "username", "avatar", "created_at")


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for the authenticated user's own profile."""

    is_muted = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "avatar",
            "is_admin",
            "is_muted",
            "muted_until",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "email",
            "is_admin",
            "muted_until",
            "created_at",
            "updated_at",
        )


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
    """Serializer for admin operations on users (list, ban, mute)."""

    is_muted = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "avatar",
            "is_admin",
            "is_active",
            "is_muted",
            "muted_until",
            "moderation_reason",
            "created_at",
        )
        read_only_fields = fields


class AdminCreateSerializer(serializers.ModelSerializer):
    """
    Serializer an admin uses to create another admin.

    Registration through /api/users/register/ can never grant is_admin, so this
    is the only path that produces a privileged account over the API.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "password", "password_confirm")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Le password non corrispondono."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(is_admin=True, **validated_data)


class BanSerializer(serializers.Serializer):
    """Payload for banning or reinstating a user."""

    banned = serializers.BooleanField(
        help_text="true per bannare l'utente, false per riattivarlo."
    )
    reason = serializers.CharField(
        required=False, allow_blank=True, max_length=500, default=""
    )

    def validate(self, attrs):
        if attrs["banned"] and not attrs.get("reason"):
            raise serializers.ValidationError({"reason": "Indica il motivo del ban."})
        return attrs


class MuteSerializer(serializers.Serializer):
    """
    Payload for muting a user for a number of hours.

    ``hours=0`` lifts an active mute.
    """

    hours = serializers.IntegerField(min_value=0, max_value=24 * 365)
    reason = serializers.CharField(
        required=False, allow_blank=True, max_length=500, default=""
    )

    def validate(self, attrs):
        if attrs["hours"] and not attrs.get("reason"):
            raise serializers.ValidationError(
                {"reason": "Indica il motivo della limitazione."}
            )
        return attrs

    def muted_until(self):
        """Resolve the payload into an expiry timestamp, or None to unmute."""
        hours = self.validated_data["hours"]
        if not hours:
            return None
        return timezone.now() + timezone.timedelta(hours=hours)
