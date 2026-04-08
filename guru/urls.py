from django.urls import path
from . import views

urlpatterns = [
    path('', views.guru_page, name='guru'),
    path('ask/', views.guru_ask, name='guru_ask'),
]
