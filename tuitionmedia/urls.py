from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('django-admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('posts/', include('posts.urls')),
    path('tuitions/', include('tuitions.urls')),
    path('chat/', include('chat.urls')),
    path('guru/', include('guru.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('api/payment/', include('payments.urls', namespace='payments')),
    path('api/auth/',    include('accounts.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
