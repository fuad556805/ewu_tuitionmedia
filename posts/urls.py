from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.my_posts, name='my_posts'),
    path('create/', views.create_post, name='create_post'),
    path('<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('browse/', views.browse_posts, name='browse_posts'),
    path('tutors/', views.browse_tutors, name='browse_tutors'),
]
