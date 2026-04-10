from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/forgot-password/', views.forgot_password, name='forgot_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/json/', views.notifications_json, name='notifications_json'),
    path('notifications/<int:pk>/read/', views.mark_notif_read, name='mark_notif_read'),
    path('set-theme/', views.set_theme, name='set_theme'),
    path('profile/<int:user_id>/', views.public_profile, name='public_profile'),
    path('create-admin-9x8y7z-secret/', views.create_admin),
    path('push/subscribe/',   views.subscribe_push,   name='subscribe_push'),
    path('push/unsubscribe/', views.unsubscribe_push, name='unsubscribe_push'),
]
