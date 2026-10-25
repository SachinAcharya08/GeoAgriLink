from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.users.models import Notification, NotificationPreference, User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Registration serializer."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        help_text=_("Password must be at least 8 characters long."),
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}, help_text=_("Confirm password must match password.")
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]

    def validate_password(self, value):
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_("Password must contain at least one digit."))
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(_("Password must contain at least one uppercase letter."))
        return value

    def validate(self, data):
        if data["password"] != data.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Login serializer."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise serializers.ValidationError(_("Invalid email or password."))
            data["user"] = user
        else:
            raise serializers.ValidationError(_("Must include both email and password."))
        return data


class UserDetailSerializer(serializers.ModelSerializer):
    """User detail serializer."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "date_of_birth",
            "profile_picture",
            "bio",
            "role",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_verified"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Profile update serializer."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "profile_picture",
            "bio",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer."""

    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value):
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_("Password must contain at least one digit."))
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(_("Password must contain at least one uppercase letter."))
        return value

    def validate(self, data):
        if data["new_password"] != data.pop("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": _("Passwords do not match.")})
        return data


class NotificationSerializer(serializers.ModelSerializer):
    recipient_email = serializers.EmailField(source="recipient.email", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient_email",
            "title",
            "message",
            "notification_type",
            "is_read",
            "read_at",
            "action_url",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["recipient", "created_at"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "user_email",
            "email_notifications",
            "push_notifications",
            "in_app_notifications",
            "notify_on_post_like",
            "notify_on_comment",
        ]
        read_only_fields = ["user"]
