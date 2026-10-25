from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.base_model import BaseModel


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, BaseModel):
    ROLE_CHOICES = [
        ("user", _("User")),
        ("admin", _("Administrator")),
        ("organizer", _("Organizer")),
    ]

    email = models.EmailField(
        _("email address"), unique=True, db_index=True, help_text=_("Required. Email must be unique.")
    )
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name=_("Phone Number"), help_text=_("Optional phone number.")
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user",
        verbose_name=_("Role"),
        help_text=_("User role for permission management."),
    )
    date_of_birth = models.DateField(blank=True, null=True, verbose_name=_("Date of Birth"))
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True, verbose_name=_("Profile Picture")
    )
    bio = models.TextField(
        blank=True, null=True, max_length=500, verbose_name=_("Biography"), help_text=_("Short biography of the user.")
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Email Verified"),
        help_text=_("Indicates whether the user has verified their email."),
    )

    last_login_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name=_("Last Login IP"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


class Notification(BaseModel):
    TYPE_CHOICES = [
        ("info", _("Info")),
        ("success", _("Success")),
        ("warning", _("Warning")),
        ("error", _("Error")),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications", verbose_name=_("Recipient")
    )
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    message = models.TextField(verbose_name=_("Message"))
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="info", verbose_name=_("Type"))
    is_read = models.BooleanField(default=False, verbose_name=_("Is Read"))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Read At"))
    action_url = models.URLField(blank=True, null=True, verbose_name=_("Action URL"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata"))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            from django.utils import timezone

            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences", verbose_name=_("User")
    )
    email_notifications = models.BooleanField(default=True, verbose_name=_("Email Notifications"))
    push_notifications = models.BooleanField(default=True, verbose_name=_("Push Notifications"))
    in_app_notifications = models.BooleanField(default=True, verbose_name=_("In-App Notifications"))
    notify_on_post_like = models.BooleanField(default=True, verbose_name=_("Notify on Post Like"))
    notify_on_comment = models.BooleanField(default=True, verbose_name=_("Notify on Comment"))

    class Meta:
        verbose_name = _("Notification Preference")
        verbose_name_plural = _("Notification Preferences")

    def __str__(self):
        return f"{self.user.email} - Preferences"
