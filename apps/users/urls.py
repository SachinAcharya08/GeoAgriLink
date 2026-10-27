from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    ChangePasswordView,
    UserLoginView,
    UserProfileView,
    UserRegistrationView,
)

router = DefaultRouter()

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("login/", UserLoginView.as_view(), name="token_obtain_pair"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("", include(router.urls)),
]
