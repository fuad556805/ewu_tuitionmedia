from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/forgot-password/', views.forgot_password, name='forgot_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notif_read, name='mark_notif_read'),
    path('set-theme/', views.set_theme, name='set_theme'),
    path('profile/<int:user_id>/', views.public_profile, name='public_profile'),
    path('create-admin-9x8y7z-secret/', views.create_admin),
]
