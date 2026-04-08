from django.urls import path
from . import views

urlpatterns = [
    path('send-request/<int:tutor_id>/', views.send_request, name='send_request'),
    path('apply/<int:post_id>/', views.apply_to_post, name='apply_to_post'),
    path('accept/<int:req_id>/', views.accept_request, name='accept_request'),
    path('tutor-accept/<int:req_id>/', views.tutor_accept_request, name='tutor_accept_request'),
    path('tutor-reject/<int:req_id>/', views.tutor_reject_request, name='tutor_reject_request'),
    path('reject/<int:req_id>/', views.reject_request, name='reject_request'),
    path('my/', views.my_tuitions, name='my_tuitions'),
    path('payments/', views.payments, name='payments'),
    path('submit-proof/<int:tuition_id>/', views.submit_proof, name='submit_proof'),
]
