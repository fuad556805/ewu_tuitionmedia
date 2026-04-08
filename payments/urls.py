from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Unified (spec-required)
    path('create/', views.UnifiedPaymentCreateView.as_view(), name='payment-create'),
    path('verify/', views.UnifiedPaymentVerifyView.as_view(), name='payment-verify'),

    # bKash
    path('bkash/create/',  views.BkashCreatePaymentView.as_view(),  name='bkash-create'),
    path('bkash/execute/', views.BkashExecutePaymentView.as_view(), name='bkash-execute'),
    path('bkash/status/',  views.BkashPaymentStatusView.as_view(),  name='bkash-status'),

    # Nagad
    path('nagad/init/',     views.NagadInitPaymentView.as_view(), name='nagad-init'),
    path('nagad/callback/', views.NagadCallbackView.as_view(),    name='nagad-callback'),

    # History / info
    path('history/',     views.MyPaymentsView.as_view(),         name='payment-history'),
    path('contacts/',    views.MyUnlockedContactsView.as_view(), name='unlocked-contacts'),
    path('commissions/', views.MyCommissionsView.as_view(),      name='commissions'),
]
