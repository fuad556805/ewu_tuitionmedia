from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('profile-approvals/', views.profile_approvals, name='profile_approvals'),
    path('profile-approvals/<int:user_id>/action/', views.approve_profile, name='approve_profile'),
    path('posts-approval/', views.posts_approval, name='posts_approval'),
    path('posts-approval/<int:post_id>/action/', views.approve_post, name='approve_post'),
    path('requests/', views.all_requests, name='all_requests'),
    path('payments/', views.payments, name='payments'),
    path('payments/set-salary/', views.set_salary, name='set_salary'),
    path('payments/<int:tuition_id>/confirm/', views.confirm_payment, name='confirm_payment'),
    path('users/', views.all_users, name='all_users'),
    path('users/<int:user_id>/toggle-ban/', views.toggle_ban, name='toggle_ban'),
    path('users/<int:user_id>/profile/', views.user_profile, name='user_profile'),
    path('inbox/', views.admin_inbox, name='admin_inbox'),
    path('inbox/send/', views.admin_send_message, name='admin_send_message'),
]