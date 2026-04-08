from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Notification

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['phone', 'get_full_name', 'role', 'profile_approved', 'banned']
    list_filter = ['role', 'profile_approved', 'banned']
    fieldsets = UserAdmin.fieldsets + (
        ('TuitionMedia', {'fields': ('role','phone','education','location','subjects','profile_approved','banned','theme')}),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'notif_type', 'read', 'created_at']
