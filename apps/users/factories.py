import factory

from apps.users.models import Notification, NotificationPreference, User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "TestPass123!")
    is_active = True
    is_verified = True


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence", nb_words=4)
    message = factory.Faker("text", max_nb_chars=200)
    notification_type = "info"
    is_read = False
    action_url = factory.Faker("url")


class NotificationPreferenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationPreference

    user = factory.SubFactory(UserFactory)
    email_notifications = True
    push_notifications = True
    in_app_notifications = True
    notify_on_post_like = True
    notify_on_comment = True
