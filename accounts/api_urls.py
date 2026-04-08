from django.urls import path
from . import api_views

urlpatterns = [
    # OTP
    path('send-otp/',   api_views.SendOTPView.as_view(),   name='auth-send-otp'),
    path('verify-otp/', api_views.VerifyOTPView.as_view(), name='auth-verify-otp'),
    path('resend-otp/', api_views.ResendOTPView.as_view(), name='auth-resend-otp'),
    path('otp-status/', api_views.OTPStatusView.as_view(), name='auth-otp-status'),

    # Login & Token
    path('login/',         api_views.LoginView.as_view(),        name='auth-login'),
    path('token/refresh/', api_views.TokenRefreshView.as_view(), name='auth-token-refresh'),

    # Forgot Password
    path('forgot-password/send/',  api_views.ForgotPasswordSendOTPView.as_view(), name='auth-forgot-send'),
    path('forgot-password/reset/', api_views.ForgotPasswordResetView.as_view(),   name='auth-forgot-reset'),

    # Profile / Me
    path('me/',      api_views.MeView.as_view(),           name='auth-me'),
    path('profile/', api_views.ProfileUpdateView.as_view(), name='auth-profile-update'),

    # Notifications
    path('notifications/',           api_views.NotificationsListView.as_view(),    name='auth-notifications'),
    path('notifications/<int:pk>/read/', api_views.MarkNotificationReadView.as_view(), name='auth-notif-read'),
]
