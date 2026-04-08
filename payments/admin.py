from django.contrib import admin
from .models import Payment, ContactUnlock, Commission


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'amount', 'method', 'status', 'purpose', 'transaction_id', 'created_at')
    list_filter   = ('method', 'status', 'purpose')
    search_fields = ('user__phone', 'payment_id', 'transaction_id')
    readonly_fields = ('raw_response', 'created_at', 'updated_at')


@admin.register(ContactUnlock)
class ContactUnlockAdmin(admin.ModelAdmin):
    list_display  = ('id', 'student', 'tutor', 'payment', 'unlocked_at')
    search_fields = ('student__phone', 'tutor__phone')


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'tutor', 'tuition', 'amount', 'paid', 'due_at', 'paid_at')
    list_filter   = ('paid',)
    search_fields = ('tutor__phone',)
