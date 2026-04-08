from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('send/', views.send_message, name='send_message'),
    path('messages/<int:user_id>/', views.get_messages, name='get_messages'),
]
