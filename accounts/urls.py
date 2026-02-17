from django.urls import path,include
from accounts.views import RegistrationView,LoginView,VerifyEmailView,PasswordResetRequestView,PasswordResetConfirmView,LogoutView,RefreshTokenView,UserProfileView


urlpatterns = [
    path('register/',RegistrationView.as_view(),name = 'register'),
    path('login/',LoginView.as_view(),name='login'),
    path('verify_email/<user_id>/<verification_token>/',VerifyEmailView.as_view(),name='verify-email'),
    path('password_reset/',PasswordResetRequestView.as_view(),name='password-reset-request'),
    path('password_reset/<user_id>/<password_reset_token>/',PasswordResetConfirmView.as_view(),name='password-reset-confirm'),
    path('logout/',LogoutView.as_view(),name='logout'),
    path('token/refresh/',RefreshTokenView.as_view(),name="regenerate-access-token"),
    path('profile/<uuid:pk>/',UserProfileView.as_view(),name='retrieve-profile'),
    path('update_profile/<uuid:pk>/',UserProfileView.as_view(),name='profile-update'),
    path('update_password/<uuid:pk>/',UserProfileView.as_view(),name='password-update'),
    
]