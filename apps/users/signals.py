from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import NotificationPreference, User


@receiver(post_save, sender=User)
def user_created_signal(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.create(
            user=instance,
            email_notifications=False,
            push_notifications=True,
            in_app_notifications=True,
            notify_on_post_like=True,
            notify_on_comment=True,
        )
