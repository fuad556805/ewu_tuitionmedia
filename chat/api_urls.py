from django.urls import path
from . import api_views

urlpatterns = [
    path('send/',                         api_views.SendMessageView.as_view(),        name='chat-send'),
    path('messages/',                     api_views.MessagesView.as_view(),           name='chat-messages'),
    path('inbox/',                        api_views.InboxSummaryView.as_view(),       name='chat-inbox'),
    path('requests/',                     api_views.ChatRequestListView.as_view(),    name='chat-requests'),
    path('requests/<int:pk>/respond/',    api_views.ChatRequestRespondView.as_view(), name='chat-request-respond'),
]
