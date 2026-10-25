import pytest

from apps.users.factories import (
    NotificationFactory,
    NotificationPreferenceFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestNotificationModel:
    def test_create_notification(self):
        notification = NotificationFactory()

        assert notification.title is not None
        assert notification.message is not None
        assert notification.recipient is not None
        assert notification.notification_type in ["info", "success", "warning", "error"]
        assert notification.is_read is False

    def test_notification_string_representation(self):
        notification = NotificationFactory(title="Test Notification")

        assert str(notification) == f"{notification.recipient.email} - Test Notification"

    def test_mark_as_read(self):
        notification = NotificationFactory(is_read=False)
        notification.mark_as_read()

        assert notification.is_read is True
        assert notification.read_at is not None

    def test_mark_already_read_notification(self):
        notification = NotificationFactory(is_read=True, read_at=None)
        notification.mark_as_read()

        assert notification.is_read is True
        assert notification.read_at is not None

    def test_notification_with_metadata(self):
        notification = NotificationFactory(metadata={"post_id": 1, "comment_id": 5})

        assert notification.metadata == {"post_id": 1, "comment_id": 5}


@pytest.mark.django_db
class TestNotificationPreferenceModel:
    def test_create_notification_preference(self):
        preference = NotificationPreferenceFactory()

        assert preference.user is not None
        assert preference.email_notifications is True
        assert preference.push_notifications is True
        assert preference.in_app_notifications is True

    def test_notification_preference_string_representation(self):
        user = UserFactory(email="test@example.com")
        preference = NotificationPreferenceFactory(user=user)

        assert str(preference) == "test@example.com - Preferences"

    def test_disable_email_notifications(self):
        preference = NotificationPreferenceFactory(email_notifications=False)

        assert preference.email_notifications is False

    def test_disable_all_notifications(self):
        preference = NotificationPreferenceFactory(
            email_notifications=False, push_notifications=False, in_app_notifications=False
        )

        assert preference.email_notifications is False
        assert preference.push_notifications is False
        assert preference.in_app_notifications is False

    def test_specific_notification_preferences(self):
        preference = NotificationPreferenceFactory(notify_on_post_like=False, notify_on_comment=True)

        assert preference.notify_on_post_like is False
        assert preference.notify_on_comment is True
