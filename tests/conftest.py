import pytest
from rest_framework.test import APIClient

from apps.users.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user():
    return UserFactory()


@pytest.fixture
def authenticated_client(authenticated_user):
    client = APIClient()
    client.force_authenticate(user=authenticated_user)
    return client


@pytest.fixture
def admin_user():
    return UserFactory(is_staff=True, is_superuser=True)
