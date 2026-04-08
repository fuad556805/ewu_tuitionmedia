from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.api_views import HomeStatsView
from payments.views import AdminBroadcastView

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # ── Template-based views (existing frontend) ──
    path('',             include('accounts.urls')),
    path('posts/',       include('posts.urls')),
    path('tuitions/',    include('tuitions.urls')),
    path('chat/',        include('chat.urls')),
    path('guru/',        include('guru.urls')),
    path('admin-panel/', include('admin_panel.urls')),

    # ── REST API ──
    path('api/auth/',    include('accounts.api_urls')),
    path('api/tuition/', include('posts.api_urls')),
    path('api/chat/',    include('chat.api_urls')),
    path('api/payment/', include('payments.urls', namespace='payments')),

    # Standalone endpoints
    path('api/home/stats/',      HomeStatsView.as_view(),      name='home-stats'),
    path('api/admin/broadcast/', AdminBroadcastView.as_view(), name='admin-broadcast'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
