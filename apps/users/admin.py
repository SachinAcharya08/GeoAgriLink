from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.users.models import Notification, NotificationPreference, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (_("Personal Info"), {"fields": ("email", "first_name", "last_name")}),
        (
            _("Profile"),
            {
                "fields": (
                    "phone_number",
                    "date_of_birth",
                    "profile_picture",
                    "bio",
                    "role",
                    "is_verified",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (
            _("Important dates"),
            {
                "fields": ("last_login", "created_at", "updated_at"),
            },
        ),
    )

    list_display = (
        "email",
        "get_full_name",
        "role",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_verified",
        "role",
        "created_at",
    )
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("created_at", "updated_at", "last_login_ip")
    ordering = ("-created_at",)

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = "Full Name"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "recipient", "title", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["title", "message", "recipient__email"]
    date_hierarchy = "created_at"
    actions = ["mark_as_read"]

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "email_notifications", "push_notifications", "in_app_notifications"]
    list_filter = ["email_notifications", "push_notifications", "in_app_notifications"]
    search_fields = ["user__email"]
