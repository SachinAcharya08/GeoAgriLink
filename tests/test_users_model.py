import pytest

from apps.users.factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = UserFactory()

        assert user.email is not None
        assert user.get_full_name() is not None
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active

    def test_create_superuser(self):
        admin = UserFactory(is_staff=True, is_superuser=True)

        assert admin.email is not None
        assert admin.is_staff
        assert admin.is_superuser

    def test_user_string_representation(self):
        user = UserFactory()

        assert str(user) == f"{user.get_full_name()} ({user.email})"
