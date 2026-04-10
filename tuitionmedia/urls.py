from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponse
import os

from accounts.api_views import HomeStatsView
from payments.views import AdminBroadcastView


def serve_sw(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    with open(sw_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')


def serve_doc(filename):
    def view(request):
        doc_path = os.path.join(settings.BASE_DIR, 'docs', filename)
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html; charset=utf-8')
    return view


urlpatterns = [
    path('sw.js', serve_sw, name='service_worker'),
    path('docs/proposal/', serve_doc('project_proposal.html'), name='doc_proposal'),
    path('docs/report/',   serve_doc('project_report.html'),   name='doc_report'),
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

] + [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
