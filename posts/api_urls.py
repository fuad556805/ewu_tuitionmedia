from django.urls import path
from . import api_views

urlpatterns = [
    path('list/',            api_views.TuitionListView.as_view(),   name='tuition-list'),
    path('create/',          api_views.TuitionCreateView.as_view(), name='tuition-create'),
    path('my/',              api_views.MyPostsView.as_view(),       name='tuition-my'),
    path('<int:pk>/',        api_views.TuitionDetailView.as_view(), name='tuition-detail'),
    path('update/<int:pk>/', api_views.TuitionUpdateView.as_view(), name='tuition-update'),
    path('<int:pk>/delete/', api_views.TuitionDeleteView.as_view(), name='tuition-delete'),
]
