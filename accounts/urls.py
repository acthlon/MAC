from django.urls import path

from accounts.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshTokenView,
    RegistrationView,
    UpdatePasswordView,
    UserProfileView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "verify-email/<uuid:user_id>/<str:verification_token>/",
        VerifyEmailView.as_view(),
        name="verify_email",
    ),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/<uuid:user_id>/<str:password_reset_token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="regenerate_access_token"),
    path("profile/<uuid:pk>/", UserProfileView.as_view(), name="retrieve_profile"),
    path("update-profile/<uuid:pk>/", UserProfileView.as_view(), name="profile_update"),
    path(
        "update-password/<uuid:pk>/",
        UpdatePasswordView.as_view(),
        name="password_update",
    ),
]
