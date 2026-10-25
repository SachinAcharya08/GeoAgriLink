from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.users.models import Notification, NotificationPreference, User


class UserService:
    """User-related business logic."""

    @staticmethod
    def register_user(email, password, first_name, last_name, **extra_fields):
        if User.objects.filter(email=email).exists():
            raise ValidationError({"email": _("A user with this email already exists.")})
        user = User.objects.create_user(
            email=email, password=password, first_name=first_name, last_name=last_name, **extra_fields
        )
        return user

    @staticmethod
    def authenticate_user(email, password):
        user = authenticate(username=email, password=password)
        return user

    @staticmethod
    def get_user_by_email(email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def update_user_profile(user, **update_fields):
        for field, value in update_fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()
        return user

    @staticmethod
    def change_password(user, old_password, new_password):
        if not user.check_password(old_password):
            raise ValidationError({"old_password": _("Current password is incorrect.")})
        user.set_password(new_password)
        user.save()

    @staticmethod
    def deactivate_user(user):
        user.is_active = False
        user.save()

    @staticmethod
    def verify_email(user):
        user.is_verified = True
        user.save()


class NotificationService:

    @staticmethod
    def create_notification(recipient, title, message, notification_type="info", action_url=None, metadata=None):
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url,
            metadata=metadata or {},
        )

    @staticmethod
    def get_user_notifications(user, unread_only=False):
        queryset = Notification.objects.filter(recipient=user)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return queryset

    @staticmethod
    def get_unread_count(user):
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @staticmethod
    def mark_as_read(notification_id):
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user):
        Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

    @staticmethod
    def get_or_create_preferences(user):
        preference, created = NotificationPreference.objects.get_or_create(user=user)
        return preference

    @staticmethod
    def should_send_notification(user, notification_type):
        try:
            prefs = NotificationPreference.objects.get(user=user)

            if not prefs.in_app_notifications:
                return False

            type_mapping = {
                "post_like": prefs.notify_on_post_like,
                "comment": prefs.notify_on_comment,
            }

            return type_mapping.get(notification_type, True)
        except NotificationPreference.DoesNotExist:
            return True
