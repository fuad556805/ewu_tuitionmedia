from django.urls import path
from . import views

urlpatterns = [
    path('', views.guru_page, name='guru'),
    path('ask/', views.guru_ask, name='guru_ask'),
    path('admin/', views.admin_guru_page, name='admin_guru'),
    path('admin/ask/', views.admin_guru_ask, name='admin_guru_ask'),
]
