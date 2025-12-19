from django.urls import path,include
from accounts.views import RegistrationView,LoginView,VerifyEmailView,PasswordResetRequestView,PasswordResetConfirmView


urlpatterns = [
    path('register/',RegistrationView.as_view(),name = 'register'),
    path('login/',LoginView.as_view(),name='login'),
    path('verify-email/<user_id>/<verification_token>',VerifyEmailView.as_view(),name='verify-email'),
    path('password-reset/',PasswordResetRequestView.as_view(),name='password-reset-request'),
    path('password-reset/<user_id>/<password_reset_token>',PasswordResetConfirmView.as_view(),name='password-reset-confirm')
    
]