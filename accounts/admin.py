from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Notification, OTPVerification


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['phone', 'get_full_name', 'role', 'profile_approved', 'banned']
    list_filter   = ['role', 'profile_approved', 'banned']
    fieldsets     = UserAdmin.fieldsets + (
        ('TuitionMedia', {
            'fields': ('role', 'phone', 'gender', 'university', 'college', 'school',
                       'department', 'location', 'subjects', 'profile_approved', 'banned', 'theme')
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'notif_type', 'read', 'created_at']


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display   = ['phone', 'is_verified', 'attempts', 'expires_at', 'created_at']
    list_filter    = ['is_verified']
    search_fields  = ['phone']
    readonly_fields = ['otp_hash', 'created_at', 'updated_at']
