from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.users.models import User


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
