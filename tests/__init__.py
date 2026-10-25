import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    def test_user_registration_success(self, api_client):
        data = {
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePassword123",
            "password_confirm": "SecurePassword123",
        }
        response = api_client.post("/api/v1/users/register/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert "tokens" in response.data
        assert response.data["user"]["email"] == data["email"]
        assert User.objects.filter(email=data["email"]).exists()

    def test_user_registration_duplicate_email(self, api_client, authenticated_user):
        data = {
            "email": authenticated_user.email,
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePassword123",
            "password_confirm": "SecurePassword123",
        }
        response = api_client.post("/api/v1/users/register/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_password_mismatch(self, api_client):
        data = {
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePassword123",
            "password_confirm": "DifferentPassword123",
        }
        response = api_client.post("/api/v1/users/register/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_weak_password(self, api_client):
        data = {
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "weak",
            "password_confirm": "weak",
        }
        response = api_client.post("/api/v1/users/register/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    def test_user_login_success(self, api_client, authenticated_user):
        data = {
            "email": authenticated_user.email,
            "password": "testpassword123",
        }
        response = api_client.post("/api/v1/users/login/", data)

        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]

    def test_user_login_invalid_credentials(self, api_client, authenticated_user):
        data = {
            "email": authenticated_user.email,
            "password": "wrongpassword",
        }
        response = api_client.post("/api/v1/users/login/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfile:
    def test_get_user_profile(self, authenticated_client):
        response = authenticated_client.get("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_200_OK
        assert "email" in response.data
        assert "first_name" in response.data
        assert "last_name" in response.data

    def test_update_user_profile(self, authenticated_client):
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "New bio",
        }
        response = authenticated_client.patch("/api/v1/users/profile/", data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"
        assert response.data["last_name"] == "Name"

    def test_unauthorized_profile_access(self, api_client):
        response = api_client.get("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChangePassword:
    def test_change_password_success(self, authenticated_client, authenticated_user):
        data = {
            "old_password": "testpassword123",
            "new_password": "NewPassword123",
            "new_password_confirm": "NewPassword123",
        }
        response = authenticated_client.put("/api/v1/users/change-password/", data)

        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old_password(self, authenticated_client):
        data = {
            "old_password": "wrongpassword",
            "new_password": "NewPassword123",
            "new_password_confirm": "NewPassword123",
        }
        response = authenticated_client.put("/api/v1/users/change-password/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
