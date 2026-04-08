from django.urls import path
from . import api_views

urlpatterns = [
    path('send-otp/',   api_views.SendOTPView.as_view(),   name='auth-send-otp'),
    path('verify-otp/', api_views.VerifyOTPView.as_view(), name='auth-verify-otp'),
    path('resend-otp/', api_views.ResendOTPView.as_view(), name='auth-resend-otp'),
    path('otp-status/', api_views.OTPStatusView.as_view(), name='auth-otp-status'),
]
